"""Provider-independent current-object backup; unsupported history fails closed."""

from pathlib import Path

from minio.error import S3Error
from minio.commonconfig import Tags

from archive import digest


def feature(client, method, *args):
    try:
        return getattr(client, method)(*args)
    except S3Error as error:
        if error.code in ("NotImplemented", "NotImplementedException"):
            return None
        raise


def current_only(client, bucket):
    version = feature(client, "get_bucket_versioning", bucket)
    if version is not None and version.status in ("Enabled", "Suspended"):
        raise ValueError("versioned_bucket_requires_version_aware_backup")


def index(client, bucket):
    return sorted(
        (obj.object_name, obj.etag, obj.size)
        for obj in client.list_objects(bucket, recursive=True)
    )


def export_buckets(client, buckets: list[str], root: Path) -> list[dict]:
    result = []
    for bi, bucket in enumerate(buckets):
        current_only(client, bucket)
        before = index(client, bucket)
        objects = []
        for oi, (key, etag, size) in enumerate(before):
            info = client.stat_object(bucket, key)
            headers = {k.lower(): v for k, v in info.metadata.items()}
            if any(
                k.startswith("x-amz-object-lock-")
                or k.startswith("x-amz-server-side-encryption")
                for k in headers
            ):
                raise ValueError("object_lock_or_sse_requires_separate_recovery_policy")
            path = root / "objects" / str(bi) / f"{oi}.bin"
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            response = client.get_object(bucket, key)
            try:
                with path.open("xb") as out:
                    while chunk := response.read(1024 * 1024):
                        out.write(chunk)
                path.chmod(0o600)
            finally:
                response.close()
                response.release_conn()
            if info.etag != etag or path.stat().st_size != size:
                raise ValueError("object_changed_during_backup")
            tags = feature(client, "get_object_tags", bucket, key)
            objects.append(
                {
                    "key": key,
                    "file": path.relative_to(root).as_posix(),
                    "sha256": digest(path),
                    "size": size,
                    "content_type": info.content_type,
                    "metadata": {
                        k[11:]: v
                        for k, v in headers.items()
                        if k.startswith("x-amz-meta-")
                    },
                    "tags": dict(tags or {}),
                }
            )
        if before != index(client, bucket):
            raise ValueError("objects_changed_during_backup")
        result.append(
            {
                "bucket": bucket,
                "version_history": "not_enabled_or_provider_unsupported",
                "objects": objects,
            }
        )
    return result


def validate_export(buckets: list[dict], root: Path) -> None:
    names = set()
    paths = set()
    for bucket in buckets:
        name = bucket["bucket"]
        if name in names:
            raise ValueError("duplicate_bucket")
        names.add(name)
        keys = set()
        for obj in bucket["objects"]:
            name = obj["file"]
            path = root / name
            if (
                not name.startswith("objects/")
                or ".." in Path(name).parts
                or path.is_symlink()
                or name in paths
                or obj["key"] in keys
                or not path.is_file()
            ):
                raise ValueError("invalid_object_manifest")
            paths.add(name)
            keys.add(obj["key"])
            if path.stat().st_size != obj["size"] or digest(path) != obj["sha256"]:
                raise ValueError("object_integrity_failed")


def require_empty(client, buckets):
    for bucket in buckets:
        if client.bucket_exists(bucket["bucket"]):
            current_only(client, bucket["bucket"])
            if index(client, bucket["bucket"]):
                raise ValueError("nonempty_object_target")


def verify_buckets(client, buckets, root):
    for bucket in buckets:
        if {key for key, _, _ in index(client, bucket["bucket"])} != {
            obj["key"] for obj in bucket["objects"]
        }:
            raise ValueError("restored_object_keys_differ")
        for obj in bucket["objects"]:
            info = client.stat_object(bucket["bucket"], obj["key"])
            response = client.get_object(bucket["bucket"], obj["key"])
            import hashlib

            h = hashlib.sha256()
            try:
                while chunk := response.read(1024 * 1024):
                    h.update(chunk)
            finally:
                response.close()
                response.release_conn()
            headers = {k.lower(): v for k, v in info.metadata.items()}
            metadata = {
                k[11:]: v for k, v in headers.items() if k.startswith("x-amz-meta-")
            }
            tags = feature(client, "get_object_tags", bucket["bucket"], obj["key"])
            if (
                h.hexdigest() != obj["sha256"]
                or info.size != obj["size"]
                or info.content_type != obj["content_type"]
                or metadata != obj["metadata"]
                or dict(tags or {}) != obj["tags"]
            ):
                raise ValueError("restored_object_fidelity_failed")


def restore_buckets(client, buckets: list[dict], root: Path) -> None:
    validate_export(buckets, root)
    require_empty(client, buckets)
    for bucket in buckets:
        name = bucket["bucket"]
        if not client.bucket_exists(name):
            client.make_bucket(name)
        for obj in bucket["objects"]:
            with (root / obj["file"]).open("rb") as body:
                client.put_object(
                    name,
                    obj["key"],
                    body,
                    obj["size"],
                    content_type=obj["content_type"],
                    metadata=obj["metadata"],
                )
            if obj["tags"]:
                tags = Tags.new_object_tags()
                tags.update(obj["tags"])
                client.set_object_tags(name, obj["key"], tags)
    verify_buckets(client, buckets, root)
