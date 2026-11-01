"""Verify reachable OCI blobs without extracting an image into the host FS.

Embedded attestations prove presence/integrity, not signer identity or trust.
"""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile


def verify_oci(path: Path, architecture: str, source: str) -> dict:
    if architecture not in ("arm64", "amd64") or not re.fullmatch(
        r"[a-f0-9]{40}", source
    ):
        raise ValueError("invalid_expected_identity")
    with tarfile.open(path, "r:*") as tar:
        members = {}
        for member in tar.getmembers():
            name = member.name.removeprefix("./")
            if member.isdir():
                continue
            if (
                not member.isfile()
                or name in members
                or PurePosixPath(name).is_absolute()
                or ".." in PurePosixPath(name).parts
            ):
                raise ValueError("unsafe_archive")
            if name not in ("oci-layout", "index.json") and not re.fullmatch(
                r"blobs/sha256/[a-f0-9]{64}", name
            ):
                raise ValueError("unexpected_archive_file")
            members[name] = member

        def document(name):
            member = members.get(name)
            if member is None or member.size > 32 * 1024 * 1024:
                raise ValueError("missing_or_large_json")
            return json.load(tar.extractfile(member))

        if document("oci-layout").get("imageLayoutVersion") != "1.0.0":
            raise ValueError("unsupported_oci_layout")
        index = document("index.json")
        verified = set()
        images, predicates = [], []
        configs = {}

        def blob(descriptor):
            digest = descriptor.get("digest", "")
            if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
                raise ValueError("invalid_digest")
            name = "blobs/sha256/" + digest[7:]
            member = members.get(name)
            if member is None or member.size != descriptor.get("size"):
                raise ValueError("blob_size_mismatch")
            if digest not in verified:
                stream = tar.extractfile(member)
                checksum = hashlib.sha256()
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    checksum.update(chunk)
                if checksum.hexdigest() != digest[7:]:
                    raise ValueError("blob_digest_mismatch")
                verified.add(digest)
            return name

        visited = set()

        def visit(descriptor, depth=0):
            if depth > 16:
                raise ValueError("deep_index")
            name = blob(descriptor)
            if descriptor["digest"] in visited:
                return
            visited.add(descriptor["digest"])
            obj = document(name)
            if "manifests" in obj:
                for child in obj["manifests"]:
                    visit(child, depth + 1)
                return
            config = document(blob(obj["config"]))
            layers = obj.get("layers", [])
            attestation = bool(layers) and all(
                layer.get("mediaType") == "application/vnd.in-toto+json"
                for layer in layers
            )
            for layer in layers:
                layer_name = blob(layer)
                if layer.get("mediaType") == "application/vnd.in-toto+json":
                    predicates.append(document(layer_name))
            if (
                not attestation
                and config.get("os") == "linux"
                and config.get("architecture") == architecture
            ):
                settings = config.get("config", {})
                if (
                    settings.get("Labels", {}).get("org.opencontainers.image.revision")
                    != source
                ):
                    raise ValueError("source_revision_mismatch")
                if settings.get("User", "").split(":")[0] in ("", "0", "root"):
                    raise ValueError("root_application_image")
                for entry in settings.get("Env", []):
                    key, _, value = entry.partition("=")
                    if value and re.search(
                        r"(?:PASSWORD|TOKEN|SECRET|LICENSE)$", key, re.I
                    ):
                        raise ValueError("credential_in_image_config")
                configs[descriptor["digest"]] = {
                    "config_digest": obj["config"]["digest"],
                    "rootfs_diff_ids": config.get("rootfs", {}).get("diff_ids", []),
                }
                images.append(
                    {
                        "digest": descriptor["digest"],
                        "size": descriptor["size"],
                        "mediaType": descriptor.get(
                            "mediaType", "application/vnd.oci.image.manifest.v1+json"
                        ),
                        "platform": {"os": "linux", "architecture": architecture},
                    }
                )

        for descriptor in index.get("manifests", []):
            visit(descriptor)
        if len(images) != 1:
            raise ValueError("expected_single_platform_image")
        if set(members) != {"oci-layout", "index.json"} | {
            "blobs/sha256/" + digest[7:] for digest in verified
        }:
            raise ValueError("unreferenced_archive_blob")
        subjects = {images[0]["digest"][7:]}
        types = {
            predicate.get("predicateType")
            for predicate in predicates
            if any(
                subject.get("digest", {}).get("sha256") in subjects
                for subject in predicate.get("subject", [])
            )
        }
        if "https://spdx.dev/Document" not in types or not any(
            str(kind).startswith("https://slsa.dev/provenance/") for kind in types
        ):
            raise ValueError("sbom_or_provenance_missing")
        return {
            "status": "verified",
            "source": source,
            "architecture": architecture,
            "descriptor": images[0],
            **configs[images[0]["digest"]],
            "verified_blobs": len(verified),
            "attestations": sorted(types),
            "signature_trust": "not_verified",
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--architecture", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = verify_oci(args.archive, args.architecture, args.source)
    args.output.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
