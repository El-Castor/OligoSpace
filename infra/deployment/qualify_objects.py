"""Qualify ONLY cached historical MinIO in a new disposable local target.

Not a production-storage decision, provider migration or format conversion.
"""

import hashlib
import io
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

BODY = b"OligoSpace disposable quarantine evidence\x00\xff"
KEY = "quarantine/original-object.bin"


def probe(action: str) -> None:
    from minio import Minio

    if not os.environ.get("PILOT_PROJECT", "").startswith("oligospace-deploy01-test-"):
        raise RuntimeError("disposable_only")
    client = Minio(
        "object-store:9000",
        access_key=os.environ["MINIO_ROOT_USER"],
        secret_key=os.environ["MINIO_ROOT_PASSWORD"],
        secure=False,
    )
    if action == "write":
        client.make_bucket("original-quarantine")
        client.put_object(
            "original-quarantine",
            KEY,
            io.BytesIO(BODY),
            len(BODY),
            content_type="application/octet-stream",
            metadata={"evidence-kind": "quarantine"},
        )
    if action == "restore":
        # Logical S3 export/import, never a copy of MinIO's internal disk format.
        response = client.get_object("original-quarantine", KEY)
        try:
            exported = response.read()
        finally:
            response.close()
            response.release_conn()
        client.make_bucket("restored-quarantine")
        client.put_object(
            "restored-quarantine",
            KEY,
            io.BytesIO(exported),
            len(exported),
            content_type="application/octet-stream",
            metadata={"evidence-kind": "quarantine"},
        )
    for bucket in (
        ["original-quarantine", "restored-quarantine"]
        if action == "restore"
        else ["original-quarantine"]
    ):
        response = client.get_object(bucket, KEY)
        try:
            assert (
                hashlib.sha256(response.read()).digest()
                == hashlib.sha256(BODY).digest()
            )
        finally:
            response.close()
            response.release_conn()
        info = client.stat_object(bucket, KEY)
        metadata = {k.lower(): v for k, v in info.metadata.items()}
        assert info.content_type == "application/octet-stream"
        assert metadata.get("x-amz-meta-evidence-kind") == "quarantine"
    print("object_probe_passed")


def main() -> None:
    context = os.environ.get("DEPLOY_TEST_CONTEXT", "default")
    docker = ["docker", "--context", context]
    endpoint = json.loads(
        subprocess.check_output(docker + ["context", "inspect", context])
    )[0]["Endpoints"]["docker"]["Host"]
    if not endpoint.startswith("unix://") or os.environ.get("DOCKER_HOST"):
        raise RuntimeError("local_context_required")
    project = "oligospace-deploy01-test-objects-" + uuid.uuid4().hex[:10]
    directory = Path(tempfile.mkdtemp(prefix=project + "-"))
    data = directory / "objects"
    data.mkdir()
    credentials = {
        "MINIO_ROOT_USER": secrets.token_hex(16),
        "MINIO_ROOT_PASSWORD": secrets.token_hex(24),
        "PILOT_PROJECT": project,
    }
    envfile = directory / "credentials.env"
    envfile.write_text("\n".join(f"{k}={v}" for k, v in credentials.items()))
    envfile.chmod(0o600)
    container = project + "-store"
    image = "minio/minio@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e"
    network_created = container_created = False

    def run(*args):
        result = subprocess.run(
            docker + list(args), capture_output=True, text=True, check=False
        )
        if result.returncode:
            raise RuntimeError("object_qualification_failed (output suppressed)")
        return result.stdout

    def client(action):
        return run(
            "run",
            "--rm",
            "--network",
            project,
            "--env-file",
            str(envfile),
            "--volume",
            f"{Path(__file__).resolve().parent}:/deployment:ro",
            "oligospace-api-tooling:latest",
            "micromamba",
            "run",
            "--name",
            "base",
            "python",
            "/deployment/qualify_objects.py",
            "--probe",
            action,
        )

    try:
        run("network", "create", "--internal", project)
        network_created = True
        run(
            "run",
            "--detach",
            "--pull=never",
            "--name",
            container,
            "--network",
            project,
            "--network-alias",
            "object-store",
            "--env-file",
            str(envfile),
            "--mount",
            f"type=bind,source={data},target=/data",
            image,
            "server",
            "/data",
        )
        container_created = True
        for _ in range(30):
            try:
                client("write")
                break
            except RuntimeError:
                time.sleep(1)
        else:
            raise RuntimeError("object_store_not_ready")
        run("restart", container)
        for _ in range(30):
            try:
                client("read")
                break
            except RuntimeError:
                time.sleep(1)
        else:
            raise RuntimeError("object_restart_failed")
        client("restore")
        assert credentials_absent_from_logs(
            docker,
            container,
            [credentials[k] for k in ("MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD")],
        )
        report = {
            "scope": "cached_arm64_minio_only",
            "image": image,
            "checks": [
                "bucket_create",
                "put_get_key_bytes_type_metadata",
                "restart_persistence",
                "logical_export_restore",
                "original_quarantine_retained",
                "credentials_not_in_logs",
            ],
            "unverified": [
                "registry_availability",
                "maintenance",
                "amd64",
                "full_offhost_restore",
            ],
        }
        (directory / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps({"report": str(directory / "report.json"), **report}))
    finally:
        if container_created:
            run("rm", "--force", container)
        if network_created:
            run("network", "rm", project)
        envfile.unlink(missing_ok=True)


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--probe":
        probe(sys.argv[2])
    else:
        main()
