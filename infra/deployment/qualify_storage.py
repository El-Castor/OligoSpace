"""Two genuinely independent, synthetic-only object stores; no pilot substitution.

AIStor is excluded by the owner's open-source-only architecture decision.
No historical bind mount, published host port, named volume or registry push.
"""

import argparse
import datetime
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import uuid

from evidence import candidate_runtime_report, credential_log_report
from storage_profiles import (
    IMAGES,
    QUALIFICATION_VARIANTS,
    image_reference,
    compose_definition,
    prepare,
    private_identity_owner_args,
)


def safe_failure(error):
    allowed = {"secret_log_gate", "network_publication", "internal_network_required"}
    reason = str(error)
    return reason if reason in allowed else "qualification_failed_details_suppressed"


def cleanup_disposable(run, containers, network, envfiles):
    failures = 0
    try:
        for name in containers:
            try:
                run("rm", "--force", name)
            except Exception:
                failures += 1
        if network:
            try:
                run("network", "rm", network)
            except Exception:
                failures += 1
    finally:
        for path in envfiles:
            path.unlink(missing_ok=True)
    return failures


def probe(action):
    from importlib.metadata import version

    from minio import Minio
    from s3_contract import export_objects, restore_objects, verify, write_cases

    if not os.environ.get("PILOT_PROJECT", "").startswith("oligospace-deploy02-test-"):
        raise ValueError("disposable_required")
    if version("minio") != "7.2.20":
        raise ValueError("application_sdk_version_mismatch")
    client = Minio(
        os.environ["S3_ENDPOINT"],
        access_key=os.environ["ACCESS_KEY"],
        secret_key=os.environ["SECRET_KEY"],
        secure=False,
    )
    bucket = "synthetic-quarantine"
    root = Path("/exchange")
    if action == "deny":
        from minio.error import S3Error

        wrong = Minio(
            os.environ["S3_ENDPOINT"],
            access_key=os.environ["ACCESS_KEY"],
            secret_key="deliberately-invalid-synthetic-secret",
            secure=False,
        )
        try:
            wrong.stat_object(bucket, next(iter(__import__("s3_contract").CASES)))
        except S3Error as error:
            if error.code not in (
                "AccessDenied",
                "SignatureDoesNotMatch",
                "InvalidAccessKeyId",
            ):
                raise ValueError("unexpected_access_error")
        else:
            raise ValueError("invalid_credential_accepted")
        print("denial_verified")
        return
    if action == "write":
        # Exercise the real adapter as well as the broader recovery contract.
        import asyncio
        from types import SimpleNamespace
        from oligospace_api.services.object_storage import ObjectStorage
        from s3_contract import CASES

        storage = ObjectStorage(
            SimpleNamespace(
                object_storage_bucket=bucket,
                object_storage_endpoint=os.environ["S3_ENDPOINT"],
                object_storage_access_key=os.environ["ACCESS_KEY"],
                object_storage_secret_key=os.environ["SECRET_KEY"],
                object_storage_secure=False,
            )
        )
        for key, (body, content_type) in CASES.items():
            asyncio.run(storage.put(key, body, content_type))
        verify(client, bucket, expected_metadata={})
        write_cases(client, bucket)
    elif action == "export":
        export_objects(client, bucket, root)
    elif action == "restore":
        restore_objects(client, bucket, root)
    verify(client, bucket)
    print("s3_contract_passed")


def runtime_command(runtime: str) -> list[str]:
    """Explicit historical activation versus the selected production runtime."""
    if runtime == "micromamba":
        return ["micromamba", "run", "--name", "base", "python"]
    if runtime == "python":
        return ["/opt/venv/bin/python"]
    raise ValueError("unsupported_runtime")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--source", choices=IMAGES, default="seaweedfs")
    parser.add_argument("--target", choices=IMAGES, default="seaweedfs")
    parser.add_argument("--seaweedfs-variant", choices=QUALIFICATION_VARIANTS)
    parser.add_argument("--api-image", required=True)
    parser.add_argument(
        "--runtime", choices=("micromamba", "python"), default="micromamba"
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.seaweedfs_variant and "seaweedfs" not in (args.source, args.target):
        parser.error("variant_requires_seaweedfs")

    def selected_image(kind):
        return image_reference(
            kind, args.seaweedfs_variant if kind == "seaweedfs" else None
        )

    docker = ["docker", "--context", args.context]
    endpoint = json.loads(
        subprocess.check_output(docker + ["context", "inspect", args.context])
    )[0]["Endpoints"]["docker"]["Host"]
    if not endpoint.startswith("unix://") or os.environ.get("DOCKER_HOST"):
        raise ValueError("local_engine_required")
    repo = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if output.is_relative_to(repo):
        raise ValueError("external_evidence_required")
    output.mkdir(parents=True, exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix="oligospace-deploy02-storage-"))
    root.chmod(0o700)
    exchange = root / "exchange"
    exchange.mkdir(mode=0o700)
    project = "oligospace-deploy02-test-" + uuid.uuid4().hex[:12]
    containers, envfiles, access_identifiers, secret_values = [], [], [], []
    network_created = False

    def run(*values):
        result = subprocess.run(
            docker + list(values),
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
        )
        if (
            result.returncode
            and values[:1] == ("rm",)
            and "No such container" in result.stderr
        ):
            return ""  # a completed --rm probe is already cleaned
        if result.returncode:
            raise RuntimeError("disposable_storage_command_failed")
        return result.stdout.strip()

    def start(kind, side):
        name = project + "-" + side
        data = root / side
        data.mkdir(mode=0o700)
        access = (
            "GK" + secrets.token_hex(16) if kind == "garage" else secrets.token_hex(16)
        )
        secret = secrets.token_hex(32)
        access_identifiers.append(access)
        secret_values.append(secret)
        profile = prepare(kind, name, data, access, secret)
        envfiles.extend(profile["private_files"])
        secret_values.extend(profile["extra_secret_values"])
        if kind == "seaweedfs":
            owner = project + "-" + side + "-config-owner"
            containers.append(owner)
            run(
                *private_identity_owner_args(
                    project, side, data / "s3.json", args.seaweedfs_variant
                )
            )
            containers.remove(owner)
        env = {
            "PILOT_PROJECT": project,
            "ACCESS_KEY": access,
            "SECRET_KEY": secret,
            "S3_ENDPOINT": f"{name}:{profile['port']}",
        }
        env.update(profile["environment"])
        path = root / (side + ".env")
        path.write_text("\n".join(k + "=" + v for k, v in env.items()))
        path.chmod(0o600)
        envfiles.append(path)
        definition = data / "compose.json"
        definition.write_text(
            json.dumps(
                compose_definition(
                    kind,
                    side,
                    project,
                    data,
                    path,
                    args.seaweedfs_variant if kind == "seaweedfs" else None,
                )
            )
        )
        containers.append(name)
        run(
            "compose",
            "--project-name",
            project,
            "--file",
            str(definition),
            "up",
            "--detach",
            "--no-build",
            "--pull",
            "never",
            side,
        )
        return name, path

    def client(path, action):
        name = project + "-probe-" + uuid.uuid4().hex[:8]
        containers.append(name)  # available for cleanup even on client timeout
        result = run(
            "run",
            "--rm",
            "--name",
            name,
            "--label",
            "org.oligospace.disposable=" + project,
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "--env",
            "HOME=/tmp",
            "--pull=never",
            "--network",
            project,
            "--env-file",
            str(path),
            "--volume",
            f"{Path(__file__).resolve().parent}:/deployment:ro",
            "--volume",
            f"{exchange}:/exchange",
            args.api_image,
            *runtime_command(args.runtime),
            "/deployment/qualify_storage.py",
            "--probe",
            action,
        )
        containers.remove(name)
        return result

    report = {
        "schema": "s3-qualification/v1",
        "project": project,
        "source": args.source,
        "target": args.target,
        "status": "failed",
        "checks": [],
        "images": {k: selected_image(k) for k in (args.source, args.target)},
        "qualification_variant": args.seaweedfs_variant,
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "application_adapter_exercised": False,
        "application_runtime": args.runtime,
        "sdk": {"name": "minio", "required_version": "7.2.20"},
        "resource_samples": {},
        "log_diagnostics": {},
        "stage": "engine_availability",
    }
    try:
        engine = json.loads(run("info", "--format", "{{json .}}"))
        # Retain bounded platform facts only, never engine configuration/environment.
        report["engine"] = {
            key: engine.get(key)
            for key in ("Architecture", "OSType", "ServerVersion", "MemTotal", "NCPU")
        }
        report["stage"] = "network_isolation"
        run(
            "network",
            "create",
            "--internal",
            "--label",
            "org.oligospace.disposable=" + project,
            project,
        )
        network_created = True
        if not json.loads(run("network", "inspect", project))[0]["Internal"]:
            raise ValueError("internal_network_required")
        report["stage"] = "candidate_start"
        source, source_env = start(args.source, "source")
        target, target_env = start(args.target, "target")
        for name in (source, target):
            if candidate_runtime_report(docker, name)["status"] != "passed":
                raise RuntimeError("disposable_candidate_not_running")
        report["stage"] = "sdk_write_read"
        for attempt in range(30):
            try:
                client(source_env, "write")
                break
            except RuntimeError:
                if attempt == 29:
                    raise
                time.sleep(1)
        report["application_adapter_exercised"] = True
        report["resource_samples"]["after_put"] = {
            name: run("stats", "--no-stream", "--format", "{{.MemUsage}}", name)
            for name in (source, target)
        }
        report["stage"] = "source_restart"
        run("restart", source)
        for attempt in range(30):
            try:
                client(source_env, "verify")
                break
            except RuntimeError:
                if attempt == 29:
                    raise
                time.sleep(1)
        report["stage"] = "logical_export_restore"
        client(source_env, "export")
        client(target_env, "restore")
        client(source_env, "deny")
        client(target_env, "deny")
        client(source_env, "verify")
        # Check the restored instance also survives a restart, independently.
        report["stage"] = "target_restart"
        run("restart", target)
        for attempt in range(30):
            try:
                client(target_env, "verify")
                break
            except RuntimeError:
                if attempt == 29:
                    raise
                time.sleep(1)
        report["stage"] = "log_network_resource_checks"
        log_gate_failed = False
        for side, name in (("source", source), ("target", target)):
            info = json.loads(run("inspect", name))[0]
            if (
                info["HostConfig"].get("PortBindings")
                or info["HostConfig"].get("NetworkMode") == "host"
            ):
                raise ValueError("network_publication")
            diagnostic = credential_log_report(
                docker, name, access_identifiers, secret_values
            )
            report["log_diagnostics"][side] = diagnostic
            log_gate_failed |= diagnostic["status"] != "passed"
        if log_gate_failed:
            raise ValueError("secret_log_gate")
        report.update(
            checks=[
                "create_bucket",
                "binary_unicode_keys",
                "sha256_contents",
                "content_types_user_metadata",
                "source_restart",
                "logical_export",
                "independent_instance_restore",
                "target_restart",
                "original_retained",
                "invalid_credentials_refused",
                "no_host_ports",
                "no_secret_in_both_log_streams",
            ],
        )
        report["resources"] = {
            name: run("stats", "--no-stream", "--format", "{{.MemUsage}}", name)
            for name in (source, target)
        }
        report["resource_samples"]["after_restore_restart"] = report["resources"]
        report["resource_measurement_scope"] = (
            "two snapshots; synthetic tiny corpus; not peak RSS or pilot capacity proof"
        )
        report["image_platforms"] = {
            kind: json.loads(
                run("image", "inspect", "--format", "{{json .}}", selected_image(kind))
            )["Architecture"]
            for kind in (args.source, args.target)
        }
        native = {
            "aarch64": "arm64",
            "arm64": "arm64",
            "x86_64": "amd64",
            "amd64": "amd64",
        }.get(report["engine"]["Architecture"])
        report["execution_mode"] = (
            "native_linux_container"
            if native
            and all(arch == native for arch in report["image_platforms"].values())
            else "emulated_or_unverified"
        )
        report["stage"] = "completed"
        report["disk_allocated_bytes"] = sum(
            p.stat().st_blocks * 512 for p in root.rglob("*") if p.is_file()
        )
        report["status"] = "passed"
    except Exception as error:
        report["status"] = (
            "blocked" if report["stage"] == "engine_availability" else "failed"
        )
        report["failure"] = safe_failure(error)
        raise
    finally:
        # Never print raw exceptions/logs/config; preserve only a sanitized report.
        runtime_failed = False
        report["runtime_diagnostics"] = {}
        for side in ("source", "target"):
            name = project + "-" + side
            if name in containers:
                diagnostic = candidate_runtime_report(docker, name)
                report["runtime_diagnostics"][side] = diagnostic
                runtime_failed |= diagnostic["status"] != "passed"
                if side not in report["log_diagnostics"]:
                    report["log_diagnostics"][side] = credential_log_report(
                        docker, name, access_identifiers, secret_values
                    )
        if runtime_failed:
            report["status"] = "failed"
        failures = cleanup_disposable(
            run, containers, project if network_created else None, envfiles
        )
        report["cleanup"] = "passed" if failures == 0 else "failed"
        if failures:
            report["status"] = "failed"
        (output / "storage-report.json").write_text(json.dumps(report, indent=2) + "\n")
        if failures:
            raise RuntimeError("disposable_cleanup_failed_credentials_removed")
        if runtime_failed:
            raise RuntimeError("disposable_candidate_runtime_failed")


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--probe":
            probe(sys.argv[2])
        else:
            main()
    except Exception:
        print("storage_qualification_failed_or_blocked", file=sys.stderr)
        raise SystemExit(1)
