"""Synthetic S3 compatibility and logical export/restore, never internal disks.

Called only by the disposable harness. No production upload policy is changed.
"""

import hashlib
import io
import json
from pathlib import Path

CASES = {
    "quarantine/binary.bin": (bytes(range(256)) * 17, "application/octet-stream"),
    "quarantine/échantillon β/ADN + 100%#?.txt": (
        "ACGT\nBrachypodium distachyon\n".encode(),
        "text/plain; charset=utf-8",
    ),
    "quarantine/spaces and %25/hash#?.dat": (
        b"\x00\xff\r\n\x00",
        "application/octet-stream",
    ),
}
META = {"evidence-kind": "quarantine", "source": "synthetic-deploy02"}


def digest(body: bytes) -> str:
    return hashlib.sha256(body).hexdigest()


def read_export(root: Path, entry: dict) -> bytes:
    name = entry["file"]
    if (
        not isinstance(name, str)
        or not name.endswith(".bin")
        or not name[:-4].isdigit()
    ):
        raise ValueError("unsafe_export_path")
    path = root / name
    if path.is_symlink():
        raise ValueError("unsafe_export_path")
    body = path.read_bytes()
    if digest(body) != entry["sha256"]:
        raise ValueError("export_checksum_mismatch")
    return body


def write_cases(client, bucket: str) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    for key, (body, content_type) in CASES.items():
        client.put_object(
            bucket,
            key,
            io.BytesIO(body),
            len(body),
            content_type=content_type,
            metadata=META,
        )


def read_object(client, bucket: str, key: str) -> bytes:
    response = client.get_object(bucket, key)
    try:
        return response.read()
    finally:
        response.close()
        response.release_conn()


def verify(client, bucket: str) -> None:
    if {obj.object_name for obj in client.list_objects(bucket, recursive=True)} != set(
        CASES
    ):
        raise ValueError("object_key_mismatch")
    for key, (body, content_type) in CASES.items():
        actual = read_object(client, bucket, key)
        info = client.stat_object(bucket, key)
        metadata = {k.lower(): v for k, v in info.metadata.items()}
        if (
            digest(actual) != digest(body)
            or actual != body
            or info.content_type != content_type
        ):
            raise ValueError("object_content_mismatch")
        if any(metadata.get("x-amz-meta-" + k) != v for k, v in META.items()):
            raise ValueError("object_metadata_mismatch")


def export_objects(client, bucket: str, root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for i, item in enumerate(
        sorted(
            client.list_objects(bucket, recursive=True), key=lambda obj: obj.object_name
        )
    ):
        body = read_object(client, bucket, item.object_name)
        info = client.stat_object(bucket, item.object_name)
        filename = f"{i}.bin"
        (root / filename).write_bytes(body)
        entries.append(
            {
                "key": item.object_name,
                "file": filename,
                "sha256": digest(body),
                "size": len(body),
                "content_type": info.content_type,
                "metadata": {
                    k.lower()[11:]: v
                    for k, v in info.metadata.items()
                    if k.lower().startswith("x-amz-meta-")
                },
            }
        )
    (root / "manifest.json").write_text(
        json.dumps(
            {"schema": "synthetic-s3-export/v1", "objects": entries},
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


def restore_objects(client, bucket: str, root: Path) -> None:
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest.get("schema") != "synthetic-s3-export/v1":
        raise ValueError("unsupported_export_schema")
    # Verify ALL bytes before any target mutation.
    objects = [(entry, read_export(root, entry)) for entry in manifest["objects"]]
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
    for entry, body in objects:
        client.put_object(
            bucket,
            entry["key"],
            io.BytesIO(body),
            len(body),
            content_type=entry["content_type"],
            metadata=entry["metadata"],
        )
