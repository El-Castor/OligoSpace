"""Compare a pinned image's Garage file to a separately downloaded public release.

Never execute or extract upstream files. Equality is a publication comparison,
not an authenticated source-to-binary attestation or runtime dependency SBOM.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import tarfile
import tempfile


LIMIT = 512 * 1024 * 1024
CHUNK = 1024 * 1024
VERSION = "2.5.0"
COMMIT = "586726edb0170bb46f604e84fba09e5659610649"
LOCK_SHA256 = "d7d15e571ad5274e849a264a04e08e7e15d49ba42d352cc7325b2847d582e61b"
TARGETS = {"amd64": "x86_64-unknown-linux-musl", "arm64": "aarch64-unknown-linux-musl"}


def release_url(architecture):
    return (
        "https://garagehq.deuxfleurs.fr/_releases/v"
        + VERSION
        + "/"
        + TARGETS[architecture]
        + "/garage"
    )


def fingerprint(stream, architecture):
    digest = hashlib.sha256()
    size = 0
    header = b""
    overlap = b""
    marker = False
    while chunk := stream.read(CHUNK):
        size += len(chunk)
        if size > LIMIT:
            raise ValueError("binary_size_limit")
        header = (header + chunk)[:64]
        digest.update(chunk)
        search = overlap + chunk
        marker |= b".dep-v0" in search
        overlap = search[-16:]
    if len(header) < 64 or header[:6] != b"\x7fELF\x02\x01":
        raise ValueError("little_endian_64bit_elf_required")
    machine = int.from_bytes(header[18:20], "little")
    if machine != {"amd64": 62, "arm64": 183}[architecture]:
        raise ValueError("elf_architecture_mismatch")
    return {
        "sha256": digest.hexdigest(),
        "size_bytes": size,
        "elf_architecture": architecture,
        "dep_v0_string_marker": "observed" if marker else "not_observed",
        "dep_v0_section_verified": False,
        "runtime_dependency_inventory": "not_verified",
    }


def _regular(tar, name, limit):
    matches = []
    for count, member in enumerate(tar):
        if count > 4096:
            raise ValueError("archive_member_limit")
        if member.name == name:
            matches.append(member)
    if len(matches) != 1 or not matches[0].isreg() or matches[0].size > limit:
        raise ValueError("unique_bounded_regular_archive_member_required")
    return tar.extractfile(matches[0])


def image_fingerprint(archive, config_digest, architecture):
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", config_digest):
        raise ValueError("config_digest_required")
    result = None
    with tarfile.open(archive) as outer:
        manifests = json.load(_regular(outer, "manifest.json", CHUNK))
        if len(manifests) != 1:
            raise ValueError("single_image_required")
        manifest = manifests[0]
        config = _regular(outer, manifest["Config"], CHUNK).read()
        if "sha256:" + hashlib.sha256(config).hexdigest() != config_digest:
            raise ValueError("config_digest_mismatch")
        metadata = json.loads(config)
        if (
            metadata.get("os") != "linux"
            or metadata.get("architecture") != architecture
        ):
            raise ValueError("config_platform_mismatch")
        layers = manifest["Layers"]
        diffs = metadata.get("rootfs", {}).get("diff_ids", [])
        if not layers or len(layers) != len(diffs):
            raise ValueError("layer_diff_ids_required")
        for layer, diff in zip(layers, diffs):
            # Docker save layers are uncompressed tar; bind them to config diff_ids.
            with tempfile.TemporaryFile() as temporary:
                source = _regular(outer, layer, LIMIT)
                digest = hashlib.sha256()
                while chunk := source.read(CHUNK):
                    digest.update(chunk)
                    temporary.write(chunk)
                if "sha256:" + digest.hexdigest() != diff:
                    raise ValueError("layer_diff_id_mismatch")
                temporary.seek(0)
                with tarfile.open(fileobj=temporary, mode="r|") as inner:
                    current = None
                    removed = False
                    for count, member in enumerate(inner):
                        if count > 4096:
                            raise ValueError("layer_member_limit")
                        name = member.name.removeprefix("./").removeprefix("/")
                        if ".." in name.split("/"):
                            raise ValueError("unsafe_layer_path")
                        if name in (".wh.garage", ".wh..wh..opq"):
                            removed = True
                        if name == "garage":
                            if not member.isreg() or member.size > LIMIT:
                                raise ValueError("garage_regular_file_required")
                            if current is not None:
                                raise ValueError("duplicate_garage_in_layer")
                            current = fingerprint(
                                inner.extractfile(member), architecture
                            )
                    if removed:
                        result = None
                    if current is not None:
                        result = current
    if result is None:
        raise ValueError("garage_file_missing")
    return result


def compare(archive, config_digest, architecture, release_binary):
    image = image_fingerprint(archive, config_digest, architecture)
    with open(release_binary, "rb") as stream:
        release = fingerprint(stream, architecture)
    matched = image["sha256"] == release["sha256"]
    return {
        "format": "garage-publication-comparison-v1",
        "architecture": architecture,
        "config_digest": config_digest,
        "image_binary": image,
        "release_binary": release,
        "official_release_url": release_url(architecture),
        "binary_match": matched,
        "observation": "same_bytes_as_public_https_release"
        if matched
        else "binary_mismatch",
        "source_tag": "v" + VERSION,
        "source_commit": COMMIT,
        "source_lockfile_sha256": LOCK_SHA256,
        "source_to_binary_provenance": "not_verified",
        "upstream_signature": "not_verified",
        "lockfile_membership_proven_by_match": False,
        "runtime_sbom": "not_verified",
        "release_authorization": "not_granted",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--config-digest", required=True)
    parser.add_argument("--architecture", choices=TARGETS, required=True)
    parser.add_argument("--release-binary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        report = compare(
            args.archive, args.config_digest, args.architecture, args.release_binary
        )
        status = 0 if report["binary_match"] else 2
    except (OSError, ValueError, KeyError, TypeError, tarfile.TarError):
        report = {
            "format": "garage-publication-comparison-v1",
            "execution": "technical_failure",
            "binary_match": False,
        }
        status = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(status)


if __name__ == "__main__":
    main()
