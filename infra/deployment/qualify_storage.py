"""Two genuinely independent, synthetic-only object stores; no pilot substitution.

AIStor is intentionally not executable without a separately authorized license.
No historical bind mount, published host port, named volume or registry push.
"""

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import tempfile
import time
import uuid

from evidence import credentials_absent_from_logs

IMAGES = {
    "minio": "minio/minio@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e",
    "seaweedfs": "chrislusf/seaweedfs@sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8",
}


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
    from minio import Minio
    from s3_contract import export_objects, restore_objects, verify, write_cases

    if not os.environ.get("PILOT_PROJECT", "").startswith("oligospace-deploy02-test-"):
        raise ValueError("disposable_required")
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
        write_cases(client, bucket)
    elif action == "export":
        export_objects(client, bucket, root)
    elif action == "restore":
        restore_objects(client, bucket, root)
    verify(client, bucket)
    print("s3_contract_passed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--source", choices=IMAGES, default="seaweedfs")
    parser.add_argument("--target", choices=IMAGES, default="seaweedfs")
    parser.add_argument("--api-image", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
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
    exchange = root / "exchange"
    exchange.mkdir(mode=0o700)
    project = "oligospace-deploy02-test-" + uuid.uuid4().hex[:12]
    containers, envfiles, passwords = [], [], []
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
        data.mkdir()
        access, secret = secrets.token_hex(16), secrets.token_hex(24)
        passwords.extend([access, secret])
        port = 9000 if kind == "minio" else 8333
        env = {
            "PILOT_PROJECT": project,
            "ACCESS_KEY": access,
            "SECRET_KEY": secret,
            "S3_ENDPOINT": f"{name}:{port}",
        }
        env.update(
            {"MINIO_ROOT_USER": access, "MINIO_ROOT_PASSWORD": secret}
            if kind == "minio"
            else {"AWS_ACCESS_KEY_ID": access, "AWS_SECRET_ACCESS_KEY": secret}
        )
        path = root / (side + ".env")
        path.write_text("\n".join(k + "=" + v for k, v in env.items()))
        path.chmod(0o600)
        envfiles.append(path)
        command = (
            ["server", "/data"]
            if kind == "minio"
            else ["mini", "-dir=/data", "-ip=" + name, "-ip.bind=0.0.0.0"]
        )
        containers.append(name)
        run(
            "run",
            "--detach",
            "--pull=never",
            "--name",
            name,
            "--label",
            "org.oligospace.disposable=" + project,
            "--network",
            project,
            "--env-file",
            str(path),
            "--mount",
            f"type=bind,source={data},target=/data",
            IMAGES[kind],
            *command,
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
            "micromamba",
            "run",
            "--name",
            "base",
            "python",
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
        "images": {k: IMAGES[k] for k in (args.source, args.target)},
    }
    try:
        run(
            "network",
            "create",
            "--internal",
            "--label",
            "org.oligospace.disposable=" + project,
            project,
        )
        network_created = True
        source, source_env = start(args.source, "source")
        target, target_env = start(args.target, "target")
        for attempt in range(30):
            try:
                client(source_env, "write")
                break
            except RuntimeError:
                if attempt == 29:
                    raise
                time.sleep(1)
        run("restart", source)
        for attempt in range(30):
            try:
                client(source_env, "verify")
                break
            except RuntimeError:
                if attempt == 29:
                    raise
                time.sleep(1)
        client(source_env, "export")
        client(target_env, "restore")
        client(source_env, "deny")
        client(target_env, "deny")
        client(source_env, "verify")
        # Check the restored instance also survives a restart, independently.
        run("restart", target)
        for attempt in range(30):
            try:
                client(target_env, "verify")
                break
            except RuntimeError:
                if attempt == 29:
                    raise
                time.sleep(1)
        for name in (source, target):
            info = json.loads(run("inspect", name))[0]
            if (
                info["HostConfig"].get("PortBindings")
                or info["HostConfig"].get("NetworkMode") == "host"
            ):
                raise ValueError("network_publication")
            if not credentials_absent_from_logs(docker, name, passwords):
                raise ValueError("secret_log_gate")
        report.update(
            status="passed",
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
        report["disk_allocated_bytes"] = sum(
            p.stat().st_blocks * 512 for p in root.rglob("*") if p.is_file()
        )
    except Exception:
        report["failure"] = "qualification_failed_details_suppressed"
        raise
    finally:
        # Never print raw exceptions/logs/config; preserve only a sanitized report.
        failures = cleanup_disposable(
            run, containers, project if network_created else None, envfiles
        )
        report["cleanup"] = "passed" if failures == 0 else "failed"
        (output / "storage-report.json").write_text(json.dumps(report, indent=2) + "\n")
        if failures:
            raise RuntimeError("disposable_cleanup_failed_credentials_removed")


if __name__ == "__main__":
    try:
        if len(sys.argv) == 3 and sys.argv[1] == "--probe":
            probe(sys.argv[2])
        else:
            main()
    except Exception:
        print("storage_qualification_failed_or_blocked", file=sys.stderr)
        raise SystemExit(1)
