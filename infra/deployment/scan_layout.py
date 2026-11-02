"""Construct a private, verified OCI directory for Trivy's OCI reader."""

import hashlib
import json
from pathlib import Path
import shutil
import tarfile

from oci import verify_oci

MAX_ARCHIVE_BYTES = 2 * 1024**3
MAX_EXPANDED_BYTES = 4 * 1024**3
MAX_MEMBERS = 20_000


def prepare_layout(archive: Path, layout: Path, architecture: str, source: str):
    # Verify the exact open-file snapshot before creating any extracted files.
    # The private copy also prevents replacement of the caller's path mid-read.
    import tempfile

    with tempfile.NamedTemporaryFile() as snapshot:
        checksum = hashlib.sha256()
        with archive.open("rb") as stream:
            if archive.stat().st_size > MAX_ARCHIVE_BYTES:
                raise ValueError("scan_archive_limit")
            copied = 0
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                copied += len(chunk)
                if copied > MAX_ARCHIVE_BYTES:
                    raise ValueError("scan_archive_limit")
                checksum.update(chunk)
                snapshot.write(chunk)
        snapshot.flush()
        snapshot.seek(0)
        expanded = 0
        with tarfile.open(fileobj=snapshot, mode="r|*") as bounded:
            for count, member in enumerate(bounded, 1):
                expanded += max(0, member.size)
                if count > MAX_MEMBERS or expanded > MAX_EXPANDED_BYTES:
                    raise ValueError("scan_expansion_limit")
        proof = verify_oci(Path(snapshot.name), architecture, source)
        snapshot.seek(0)
        layout.mkdir(mode=0o700)
        with tarfile.open(fileobj=snapshot, mode="r:*") as tar:
            for member in tar.getmembers():
                if member.isdir():
                    continue
                # verify_oci already rejects links, duplicates and unsafe names.
                target = layout / member.name.removeprefix("./")
                target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                with target.open("xb") as output:
                    shutil.copyfileobj(tar.extractfile(member), output)
        index = json.dumps(
            {"schemaVersion": 2, "manifests": [proof["descriptor"]]},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        (layout / "index.json").write_bytes(index)
        return {
            **proof,
            "archive_sha256": checksum.hexdigest(),
            "view_index_sha256": hashlib.sha256(index).hexdigest(),
        }
