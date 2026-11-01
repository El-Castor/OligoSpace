"""Anonymous public-registry metadata only. No image layer/license/private token.

Observation is not a release decision or signature/maintenance verification.
"""

import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import urllib.error
import urllib.request

REFERENCES = {
    "minio_historical": "minio/minio:RELEASE.2025-09-07T16-13-09Z",
    "aistor": "quay.io/minio/aistor/minio:RELEASE.2026-09-19T17-05-25Z",
    "seaweedfs": "chrislusf/seaweedfs:4.51",
    "postgres": "postgres:17.11-alpine",
    "redis": "redis:7.4.10-alpine",
    "keycloak": "quay.io/keycloak/keycloak:26.7.2",
    "caddy": "caddy:2.11.4-alpine",
    "micromamba": "mambaorg/micromamba:2.4.0",
    "node": "node:22.23.0-alpine3.23",
    "scanner": "aquasec/trivy:0.76.1",
    "sbom_scanner": "docker/buildkit-syft-scanner:stable-1",
}


def reference_parts(reference):
    if "@sha256:" in reference:
        repo, tag = reference.split("@", 1)
    else:
        repo, tag = reference.rsplit(":", 1)
        if tag == "latest" or not tag:
            raise ValueError("mutable_reference")
    if repo.startswith("quay.io/"):
        return "quay.io", repo[len("quay.io/") :], tag
    if repo.startswith("docker.io/"):
        repo = repo[len("docker.io/") :]
    if "." in repo.split("/")[0]:
        raise ValueError("unapproved_public_registry")
    return "registry-1.docker.io", repo if "/" in repo else "library/" + repo, tag


def verify_manifest(raw, expected_digest):
    actual = "sha256:" + hashlib.sha256(raw).hexdigest()
    if actual != expected_digest:
        raise ValueError("manifest_digest_mismatch")
    obj = json.loads(raw)
    platforms = {}
    for descriptor in obj.get("manifests", []):
        platform = descriptor.get("platform", {})
        if platform.get("os") == "linux" and platform.get("architecture") in (
            "arm64",
            "amd64",
        ):
            digest = descriptor.get("digest", "")
            if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
                raise ValueError("invalid_platform_digest")
            platforms[platform["architecture"]] = digest
    return {
        "digest": actual,
        "platforms": platforms,
        "media_type": obj.get("mediaType"),
    }


def inspect_public(reference):
    host, repo, tag = reference_parts(reference)
    headers = {
        "User-Agent": "OligoSpace-DEPLOY02",
        "Accept": "application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.manifest.v1+json",
    }
    if host == "registry-1.docker.io":
        with urllib.request.urlopen(
            "https://auth.docker.io/token?service=registry.docker.io&scope=repository:"
            + repo
            + ":pull",
            timeout=20,
        ) as response:
            headers["Authorization"] = "Bearer " + json.load(response)["token"]
    url = "https://" + host + "/v2/" + repo + "/manifests/" + tag
    try:
        with urllib.request.urlopen(
            urllib.request.Request(url, headers=headers), timeout=30
        ) as response:
            raw = response.read(16 * 1024 * 1024 + 1)
            if len(raw) > 16 * 1024 * 1024:
                raise ValueError("manifest_too_large")
            expected = response.headers.get(
                "Docker-Content-Digest", "sha256:" + hashlib.sha256(raw).hexdigest()
            )
        if tag.startswith("sha256:") and tag != expected:
            raise ValueError("requested_digest_mismatch")
        return {
            "reference": reference,
            "status": "metadata_verified",
            **verify_manifest(raw, expected),
        }
    except urllib.error.HTTPError as error:
        return {"reference": reference, "status": "blocked", "http_status": error.code}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = {
        "observed_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "images": {},
    }
    for role, reference in REFERENCES.items():
        try:
            report["images"][role] = inspect_public(reference)
        except Exception:
            report["images"][role] = {
                "reference": reference,
                "status": "blocked",
                "reason": "metadata_unavailable",
            }
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print("public_metadata_report_written; not_a_release_approval")


if __name__ == "__main__":
    main()
