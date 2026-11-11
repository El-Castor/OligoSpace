"""Read-only local pilot preflight. Never starts, deploys or prints secrets."""

import argparse
import hashlib
import importlib.metadata
import sys
import json
import os
from pathlib import Path
import shutil
import stat
import ipaddress
import subprocess
from urllib.parse import urlparse

from policy import validate
from release import blockers, image_contract_matches

ROOT = Path(__file__).resolve().parent


def mandatory_blockers():
    # No caller-supplied JSON can turn these outstanding owner/security gates green.
    return ["AUTH_B6", "OWNER_PILOT_AUTHORIZATION"]


def protected_file(path: Path, *, secret=False):
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        return False
    info = path.stat()
    return (
        info.st_uid in (os.getuid(), 0)
        and info.st_nlink == 1
        and stat.S_IMODE(info.st_mode) & 0o022 == 0
        and (not secret or stat.S_IMODE(info.st_mode) & 0o077 == 0)
    )


def command(args):
    result = subprocess.run(
        args, capture_output=True, stdin=subprocess.DEVNULL, timeout=30, check=False
    )
    if result.returncode:
        raise ValueError("read_only_probe_failed")
    return result.stdout


def certificate_checks(certificate: Path, key: Path, ca: Path, hostname: str):
    checks = {}
    if (
        not all(protected_file(p) for p in (certificate, key, ca))
        or key.stat().st_mode & 0o007
    ):
        return {"tls_files": "FAIL", "tls_chain_name_expiry_key": "NOT_VERIFIED"}
    checks["tls_files"] = "PASS"
    try:
        command(
            [
                "openssl",
                "verify",
                "-CAfile",
                str(ca),
                "-untrusted",
                str(certificate),
                "-purpose",
                "sslserver",
                str(certificate),
            ]
        )
        from cryptography import x509
        from datetime import UTC, datetime, timedelta

        cert = x509.load_pem_x509_certificate(certificate.read_bytes())
        names = cert.extensions.get_extension_for_class(
            x509.SubjectAlternativeName
        ).value
        normalized = hostname.encode("idna").decode().lower().rstrip(".")
        matches = False
        for name in names.get_values_for_type(x509.DNSName):
            name = name.encode("idna").decode().lower().rstrip(".")
            matches |= name == normalized or (
                name.startswith("*.")
                and name.count("*") == 1
                and normalized.endswith(name[1:])
                and normalized.count(".") == name.count(".")
            )
        try:
            address = ipaddress.ip_address(normalized)
            matches = address in names.get_values_for_type(x509.IPAddress)
        except ValueError:
            pass
        if not matches:
            raise ValueError("certificate_name_mismatch")
        if cert.not_valid_after_utc < datetime.now(UTC) + timedelta(days=1):
            raise ValueError("certificate_expiring")
        public = command(
            ["openssl", "x509", "-in", str(certificate), "-noout", "-pubkey"]
        )
        private = command(["openssl", "pkey", "-in", str(key), "-pubout"])
        checks["tls_chain_name_expiry_key"] = (
            "PASS"
            if hashlib.sha256(public).digest() == hashlib.sha256(private).digest()
            else "FAIL"
        )
    except Exception:
        checks["tls_chain_name_expiry_key"] = "FAIL"
    return checks


def template_checks(config):
    checks = {}
    bindings = {
        v["target"]: Path(v["source"])
        for service in config["services"].values()
        for v in service.get("volumes", [])
        if isinstance(v, dict) and v.get("type") == "bind"
    }
    for key, target, template in [
        ("proxy_template", "/etc/caddy/Caddyfile", "Caddyfile.template"),
        ("identity_template", "/etc/oligospace/keycloak.conf", "keycloak.conf.example"),
    ]:
        p = bindings.get(target)
        checks[key] = (
            "PASS"
            if p
            and protected_file(p)
            and p.read_bytes() == (ROOT / template).read_bytes()
            else "FAIL"
        )
    try:
        checks.update(
            certificate_checks(
                bindings["/etc/oligospace/tls/cert.pem"],
                bindings["/etc/oligospace/tls/key.pem"],
                bindings["/certs/ca.pem"],
                urlparse(
                    config["services"]["web"]["environment"]["NEXTAUTH_URL"]
                ).hostname,
            )
        )
    except (KeyError, TypeError, OSError):
        checks["tls_chain_name_expiry_key"] = "NOT_VERIFIED"
    return checks


def namespace_checks(docker, config, project):
    """Read metadata only: never mount or inspect volume contents."""
    checks = {"target_namespace": "NOT_VERIFIED", "ingress_port": "NOT_VERIFIED"}
    try:
        volumes = command(
            docker
            + [
                "volume",
                "ls",
                "--filter",
                "name=" + project + "_",
                "--format",
                "{{.Name}}",
            ]
        )
        networks = command(
            docker
            + [
                "network",
                "ls",
                "--filter",
                "name=" + project + "_",
                "--format",
                "{{.Name}}",
            ]
        )
        containers = command(
            docker
            + [
                "ps",
                "--all",
                "--filter",
                "label=com.docker.compose.project=" + project,
                "--quiet",
            ]
        )
        checks["target_namespace"] = (
            "BLOCKED"
            if volumes.strip() or networks.strip() or containers.strip()
            else "PASS"
        )
        # Docker listeners only; native/host listeners cannot be inferred from this.
        occupied = command(docker + ["ps", "--filter", "publish=443", "--quiet"])
        checks["ingress_docker_port"] = "BLOCKED" if occupied.strip() else "PASS"
    except (OSError, ValueError, subprocess.TimeoutExpired):
        pass
    return checks


def diagnose(
    context,
    env_file,
    project,
    evidence=None,
    *,
    min_memory_gib=8,
    min_disk_gib=12,
    min_cpus=2,
):
    checks = {
        "docker_compose": "NOT_VERIFIED",
        "configuration": "NOT_VERIFIED",
        "image_architecture": "NOT_VERIFIED",
        "capacity_memory": "NOT_VERIFIED",
        "capacity_host_disk": "NOT_VERIFIED",
        "capacity_engine_disk": "NOT_VERIFIED",
        "dns_live_tls": "NOT_VERIFIED",
        "backup_keys_destination_vault": "NOT_VERIFIED",
        "real_storage_provider": "BLOCKED",
        "real_cloudflare": "NOT_VERIFIED",
    }
    rules = []
    if (
        not protected_file(env_file, secret=True)
        or os.environ.get("DOCKER_HOST")
        or os.environ.get("DOCKER_CONTEXT")
    ):
        raise ValueError("protected_local_inputs_required")
    if min_memory_gib <= 0 or min_disk_gib <= 0 or min_cpus < 1:
        raise ValueError("positive_capacity_thresholds_required")
    docker = ["docker", "--context", context]
    endpoint = json.loads(command(docker + ["context", "inspect", context]))[0][
        "Endpoints"
    ]["docker"]["Host"]
    if not endpoint.startswith("unix://"):
        raise ValueError("local_context_required")
    command(docker + ["compose", "version", "--short"])
    info = json.loads(command(docker + ["info", "--format", "{{json .}}"]))
    checks["docker_compose"] = "PASS"
    checks["capacity_cpu"] = "PASS" if info.get("NCPU", 0) >= min_cpus else "FAIL"
    checks["capacity_memory"] = (
        "PASS" if info.get("MemTotal", 0) >= min_memory_gib * 1024**3 else "FAIL"
    )
    checks["capacity_host_disk"] = (
        "PASS"
        if shutil.disk_usage(env_file.parent).free >= min_disk_gib * 1024**3
        else "FAIL"
    )
    engine = Path(info.get("DockerRootDir", "/nonexistent"))
    try:
        if engine.is_dir():
            checks["capacity_engine_disk"] = (
                "PASS"
                if shutil.disk_usage(engine).free >= min_disk_gib * 1024**3
                else "FAIL"
            )
    except OSError:
        checks["capacity_engine_disk"] = "NOT_VERIFIED"
    dc = docker + [
        "compose",
        "--project-name",
        project,
        "--env-file",
        str(env_file),
        "--file",
        str(ROOT / "compose.pilot.json"),
        "--profile",
        "operations",
    ]
    config = json.loads(command(dc + ["config", "--format", "json"]))
    rules = validate(config)
    checks["configuration"] = "FAIL" if rules else "PASS"
    checks.update(template_checks(config))
    checks.update(namespace_checks(docker, config, project))
    if config.get("name") != project:
        rules.append("explicit_project_mismatch")
        checks["configuration"] = "FAIL"
    native = {
        "aarch64": "arm64",
        "arm64": "arm64",
        "x86_64": "amd64",
        "amd64": "amd64",
    }.get(info.get("Architecture"))
    images = []
    for reference in sorted({s["image"] for s in config["services"].values()}):
        try:
            image = json.loads(command(docker + ["image", "inspect", reference]))[0]
            images.append(
                image.get("Architecture") == native
                and image.get("Os") == "linux"
                and reference in image.get("RepoDigests", [])
            )
        except (ValueError, OSError, KeyError, subprocess.TimeoutExpired):
            images.append(False)
    checks["image_architecture"] = "PASS" if images and all(images) else "NOT_VERIFIED"
    manifest = (
        json.loads(evidence.read_text())
        if evidence and protected_file(evidence)
        else {}
    )
    pending = blockers(manifest)
    if not image_contract_matches(config, manifest):
        pending.append("manifest_config_images")
    # Backup code/dependencies are present; actual keys/vault/destination remain external.
    checks["backup_commands"] = (
        "PASS"
        if all(
            (ROOT.parent / "backup" / name).is_file()
            for name in [
                "recovery.py",
                "archive.py",
                "s3.py",
                "retention.py",
                "requirements.txt",
            ]
        )
        else "FAIL"
    )
    try:
        checks["backup_operator_dependencies"] = (
            "PASS"
            if sys.version_info >= (3, 12)
            and importlib.metadata.version("cryptography") == "50.0.2"
            and importlib.metadata.version("minio") == "7.2.20"
            else "FAIL"
        )
    except importlib.metadata.PackageNotFoundError:
        checks["backup_operator_dependencies"] = "NOT_VERIFIED"
    checks["container_secret_access"] = "NOT_VERIFIED"
    pending = sorted(set(pending + mandatory_blockers()))
    checks.update({rule: "BLOCKED" for rule in pending})
    return {
        "schema": "oligospace-private-pilot-preflight/v1",
        "checks": checks,
        "rules": sorted(set(rules)),
        "static": "failed"
        if rules or any(v == "FAIL" for v in checks.values())
        else "passed",
        "activation": "BLOCKED",
        "release": "blocked",
        "unverified": pending,
        "deployed": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--release-evidence", type=Path)
    parser.add_argument("--min-cpus", type=int, default=2)
    parser.add_argument("--min-memory-gib", type=float, default=8)
    parser.add_argument("--min-disk-gib", type=float, default=12)
    args = parser.parse_args()
    try:
        report = diagnose(
            args.context,
            args.env_file,
            args.project,
            args.release_evidence,
            min_memory_gib=args.min_memory_gib,
            min_disk_gib=args.min_disk_gib,
            min_cpus=args.min_cpus,
        )
    except Exception:
        report = {
            "checks": {"preflight": "FAIL"},
            "static": "failed",
            "rules": ["preflight_refused"],
            "activation": "BLOCKED",
            "release": "blocked",
            "deployed": False,
        }
    print(json.dumps(report))
    return 1  # No real activation authorized or implemented in this lot.


if __name__ == "__main__":
    raise SystemExit(main())
