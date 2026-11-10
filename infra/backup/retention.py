"""Verified encrypted transfer and opt-in retention; no schedules or remote shell."""

import argparse
import json
import os
from pathlib import Path
import tempfile
import time

from archive import digest, unseal, CHUNK, fsync_directory


def verify(path, key):
    with tempfile.TemporaryDirectory(prefix="oligospace-retention-") as directory:
        unseal(path, Path(directory) / "verified", key)


def transfer(source: Path, destination: Path, key_file: Path) -> str:
    verify(source, key_file)
    directory = destination.parent
    if (
        directory.is_symlink()
        or not directory.is_dir()
        or directory.stat().st_mode & 0o077
    ):
        raise ValueError("private_destination_required")
    fd, name = tempfile.mkstemp(prefix=".oligospace-transfer-", dir=directory)
    try:
        with source.open("rb") as inp, os.fdopen(fd, "wb") as out:
            while chunk := inp.read(CHUNK):
                out.write(chunk)
            out.flush()
            os.fsync(out.fileno())
        if digest(source) != digest(Path(name)):
            raise ValueError("transfer_checksum_failed")
        verify(Path(name), key_file)
        os.link(name, destination)
        fsync_directory(directory)
        return digest(destination)
    finally:
        Path(name).unlink(missing_ok=True)


def prune(
    directory: Path,
    key_file: Path,
    *,
    keep: int,
    minimum_age_days: int,
    apply: bool = False,
) -> int:
    if (
        keep < 1
        or minimum_age_days < 0
        or directory.is_symlink()
        or directory.stat().st_mode & 0o077
    ):
        raise ValueError("unsafe_retention_policy")
    paths = sorted(
        directory.glob("*.osbk"), key=lambda path: path.stat().st_mtime, reverse=True
    )
    # Every point, including newest, must authenticate before any deletion.
    fingerprints = {}
    for path in paths:
        if path.is_symlink() or path.stat().st_nlink != 1:
            raise ValueError("unsafe_retention_member")
        verify(path, key_file)
        fingerprints[path] = digest(path)
    candidates = [
        p
        for p in paths[keep:]
        if time.time() - p.stat().st_mtime >= minimum_age_days * 86400
    ]
    if apply:
        for path in candidates:
            if path.is_symlink() or digest(path) != fingerprints[path]:
                raise ValueError("retention_point_changed")
        for path in candidates:
            path.unlink()
        fsync_directory(directory)
    return len(candidates)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["transfer", "prune"])
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--keep", type=int)
    parser.add_argument("--minimum-age-days", type=int)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        if args.action == "transfer":
            result = {"sha256": transfer(args.source, args.destination, args.key_file)}
        else:
            result = {
                "eligible": prune(
                    args.destination,
                    args.key_file,
                    keep=args.keep,
                    minimum_age_days=args.minimum_age_days,
                    apply=args.apply,
                ),
                "applied": args.apply,
            }
        print(json.dumps({"status": "passed", **result}))
        return 0
    except Exception:
        print('{"status":"failed","rule":"retention_or_transfer_refused"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
