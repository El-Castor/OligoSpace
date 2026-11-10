"""Private, authenticated recovery envelope. No credentials in diagnostics."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tarfile
import tempfile

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

MAGIC = b"OLIGOSPACE-BACKUP-1\n"
CHUNK = 1024 * 1024


def fsync_directory(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def protected(path: Path) -> None:
    if (
        path.is_symlink()
        or not path.is_file()
        or path.stat().st_uid != os.getuid()
        or stat.S_IMODE(path.stat().st_mode) & 0o077
    ):
        raise ValueError("protected_file_required")


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(CHUNK):
            h.update(chunk)
    return h.hexdigest()


def key_bytes(path: Path) -> bytes:
    protected(path)
    value = path.read_bytes()
    if len(value) != 32:
        raise ValueError("key_must_be_32_random_bytes")
    return value


def manifest_files(root: Path) -> dict:
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or (not path.is_file() and not path.is_dir()):
            raise ValueError("unsafe_member")
        if path.is_file() and path.relative_to(root).as_posix() != "manifest.json":
            files[path.relative_to(root).as_posix()] = {
                "sha256": digest(path),
                "size": path.stat().st_size,
            }
    return files


def validate_tree(root: Path) -> dict:
    manifest = json.loads((root / "manifest.json").read_text())
    if manifest.get("schema") != "oligospace-recovery/v1" or manifest.get(
        "files"
    ) != manifest_files(root):
        raise ValueError("archive_integrity_failed")
    return manifest


def seal(root: Path, destination: Path, key_file: Path) -> None:
    key = key_bytes(key_file)
    validate_tree(root)
    if destination.exists() or destination.is_symlink():
        raise ValueError("destination_exists")
    # Plain staging is private, short lived and never a CI artifact.
    with tempfile.TemporaryDirectory(prefix="oligospace-recovery-") as tmp:
        tarpath = Path(tmp) / "payload.tar"
        with tarfile.open(tarpath, "w") as tar:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    tar.add(
                        path, arcname=path.relative_to(root).as_posix(), recursive=False
                    )
        nonce = os.urandom(12)
        enc = Cipher(algorithms.AES(key), modes.GCM(nonce)).encryptor()
        enc.authenticate_additional_data(MAGIC)
        fd, name = tempfile.mkstemp(
            prefix=".oligospace-partial-", dir=destination.parent
        )
        try:
            with os.fdopen(fd, "wb") as out, tarpath.open("rb") as inp:
                out.write(MAGIC + nonce)
                while chunk := inp.read(CHUNK):
                    out.write(enc.update(chunk))
                out.write(enc.finalize())
                out.write(enc.tag)
                out.flush()
                os.fsync(out.fileno())
            # link is atomic and cannot overwrite an existing recovery point.
            os.link(name, destination)
            fsync_directory(destination.parent)
        finally:
            Path(name).unlink(missing_ok=True)


def unseal(
    archive: Path, destination: Path, key_file: Path, max_bytes: int = 64 * 1024**3
) -> dict:
    key = key_bytes(key_file)
    if destination.exists() or destination.is_symlink():
        raise ValueError("destination_exists")
    if archive.stat().st_size > max_bytes or archive.stat().st_size < len(MAGIC) + 28:
        raise ValueError("archive_size_invalid")
    with tempfile.TemporaryDirectory(prefix="oligospace-recovery-") as tmp:
        plain = Path(tmp) / "payload.tar"
        try:
            with archive.open("rb") as inp, plain.open("wb") as out:
                if inp.read(len(MAGIC)) != MAGIC:
                    raise ValueError("archive_format_invalid")
                nonce = inp.read(12)
                inp.seek(-16, 2)
                tag = inp.read(16)
                remaining = inp.tell() - 16 - len(MAGIC) - 12
                inp.seek(len(MAGIC) + 12)
                dec = Cipher(algorithms.AES(key), modes.GCM(nonce, tag)).decryptor()
                dec.authenticate_additional_data(MAGIC)
                while remaining:
                    chunk = inp.read(min(CHUNK, remaining))
                    if not chunk:
                        raise ValueError("archive_truncated")
                    remaining -= len(chunk)
                    out.write(dec.update(chunk))
                out.write(dec.finalize())
            # Authentication completed BEFORE interpreting or extracting plaintext.
            stage = Path(tmp) / "tree"
            stage.mkdir(mode=0o700)
            seen = set()
            total = 0
            with tarfile.open(plain, "r:") as tar:
                for member in tar:
                    name = member.name
                    if (
                        not member.isfile()
                        or name.startswith("/")
                        or ".." in Path(name).parts
                        or name in seen
                        or "\\" in name
                    ):
                        raise ValueError("unsafe_member")
                    seen.add(name)
                    total += member.size
                    if total > max_bytes:
                        raise ValueError("archive_size_invalid")
                    target = stage / name
                    target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
                    source = tar.extractfile(member)
                    if source is None:
                        raise ValueError("missing_member")
                    with target.open("xb") as output:
                        shutil.copyfileobj(source, output, CHUNK)
                    target.chmod(0o600)
            manifest = validate_tree(stage)
            shutil.copytree(stage, destination)
            return manifest
        except Exception as error:
            raise ValueError("archive_authentication_or_integrity_failed") from error
