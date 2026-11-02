"""Observe pinned upstream storage images; never authorize deployment or trust."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

from scan_artifact import SCANNER, failure, safe_field, summarize_findings
from storage_profiles import IMAGES


def verified_json(data, digest):
    # buildx may append one display newline to the registry's original bytes.
    for payload in (data, data.removesuffix(b"\n")):
        if "sha256:" + hashlib.sha256(payload).hexdigest() == digest:
            return json.loads(payload)
    raise ValueError("registry_digest_mismatch")


def platform_descriptor(index, architecture):
    matches = [
        item
        for item in index.get("manifests", [])
        if item.get("platform", {}).get("os") == "linux"
        and item.get("platform", {}).get("architecture") == architecture
    ]
    if len(matches) != 1 or not re.fullmatch(
        r"sha256:[0-9a-f]{64}", matches[0].get("digest", "")
    ):
        raise ValueError("unique_pinned_platform_required")
    return matches[0]


def verify_archive(archive, config_digest, architecture):
    # Never extract upstream archives to the host filesystem.
    with tarfile.open(archive) as tar:
        manifests = json.load(tar.extractfile("manifest.json"))
        if len(manifests) != 1:
            raise ValueError("single_image_required")
        config = tar.extractfile(manifests[0]["Config"]).read()
        if "sha256:" + hashlib.sha256(config).hexdigest() != config_digest:
            raise ValueError("config_digest_mismatch")
        metadata = json.loads(config)
        if (
            metadata.get("os") != "linux"
            or metadata.get("architecture") != architecture
        ):
            raise ValueError("config_platform_mismatch")


def inventory(raw):
    packages = []
    licenses = []
    for result in raw.get("Results", []):
        for package in result.get("Packages", []):
            packages.append(
                {
                    "name": safe_field(package["Name"]),
                    "version": safe_field(package["Version"]),
                    "licenses": [safe_field(v) for v in package.get("Licenses", [])],
                }
            )
        for license_finding in result.get("Licenses", []):
            licenses.append(
                {
                    "name": safe_field(license_finding["Name"]),
                    "severity": safe_field(license_finding["Severity"]),
                }
            )
    return {
        "format": "sanitized-package-inventory-v1",
        "packages": packages,
        "licenses": licenses,
        "license_findings": len(licenses),
        "license_coverage": "observed" if packages else "not_verified",
    }


def run(command, timeout=1200):
    return subprocess.check_output(command, stderr=subprocess.PIPE, timeout=timeout)


def summarize_candidate(raw, proof, database):
    if raw.get("SchemaVersion") != 2 or raw.get("ArtifactType") != "container_image":
        raise ValueError("invalid_report_schema")
    metadata = raw.get("Metadata", {})
    config = metadata.get("ImageConfig", {})
    if metadata.get("ImageID") != proof["config_digest"]:
        raise ValueError("report_identity_mismatch")
    if (
        config.get("os") != "linux"
        or config.get("architecture") != proof["architecture"]
    ):
        raise ValueError("report_platform_mismatch")
    if database.get("Version") != 2 or not all(
        isinstance(database.get(key), str)
        and re.fullmatch(r"[0-9T:Z.+-]+", database[key])
        for key in ("UpdatedAt", "NextUpdate", "DownloadedAt")
    ):
        raise ValueError("database_metadata_missing")
    report = summarize_findings(raw)
    report["sbom"] = inventory(raw)
    operating_system = metadata.get("OS", {})
    language_packages = sum(
        len(result.get("Packages", []))
        for result in raw.get("Results", [])
        if result.get("Class") == "lang-pkgs"
    )
    report["coverage"] = {
        "operating_system": "detected"
        if operating_system.get("Family")
        else "not_detected",
        "language_packages": language_packages,
        "package_inventory": "observed"
        if report["sbom"]["packages"]
        else "not_verified",
        "missing_os_metadata_is_scratch_proof": False,
    }
    report["vulnerability_database"] = {
        key: database[key]
        for key in ("Version", "UpdatedAt", "NextUpdate", "DownloadedAt")
    }
    if report["sbom"]["license_findings"]:
        report.update(execution="completed_with_findings", gate="failed")
    if not report["sbom"]["packages"] or (
        not operating_system.get("Family") and not language_packages
    ):
        report["rule_id"] = "CANDIDATE_PACKAGE_COVERAGE_MISSING"
        if report["gate"] != "failed":
            report.update(execution="technical_failure", gate="not_verified")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", choices=("seaweedfs", "garage"), required=True)
    parser.add_argument("--architecture", choices=("arm64", "amd64"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = failure("CANDIDATE_SCAN_NOT_EXECUTED", "not_executed")
    proof = {}
    stage = "CANDIDATE_IDENTITY_FAILED"
    try:
        if os.environ.get("DOCKER_HOST") or os.environ.get("DOCKER_CONTEXT"):
            raise ValueError("default_local_engine_required")
        endpoint = json.loads(run(["docker", "context", "inspect"]))[0]["Endpoints"][
            "docker"
        ]["Host"]
        if not endpoint.startswith("unix://"):
            raise ValueError("local_engine_required")
        image = IMAGES[args.candidate]
        index = verified_json(
            run(["docker", "buildx", "imagetools", "inspect", "--raw", image]),
            image.split("@")[1],
        )
        descriptor = platform_descriptor(index, args.architecture)
        child = image.split("@")[0] + "@" + descriptor["digest"]
        manifest = verified_json(
            run(["docker", "buildx", "imagetools", "inspect", "--raw", child]),
            descriptor["digest"],
        )
        config_digest = manifest["config"]["digest"]
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", config_digest):
            raise ValueError("config_digest_required")
        proof = {"architecture": args.architecture, "config_digest": config_digest}
        report.update({"index_reference": image, "platform_reference": child, **proof})
        run(["docker", "pull", "--platform", "linux/" + args.architecture, child])
        with tempfile.TemporaryDirectory(
            prefix="oligospace-candidate-scan-"
        ) as directory:
            root = Path(directory)
            archive = root / "image.tar"
            run(["docker", "image", "save", "--output", str(archive), child])
            verify_archive(archive, config_digest, args.architecture)
            (root / "cache").mkdir(mode=0o700)
            stage = "CANDIDATE_SCANNER_FAILED"
            # No Docker socket. Raw findings exist only in captured process memory.
            raw = json.loads(
                run(
                    [
                        "docker",
                        "run",
                        "--rm",
                        "--cap-drop=ALL",
                        "--security-opt=no-new-privileges",
                        "--read-only",
                        "--tmpfs",
                        "/tmp:rw,nosuid,nodev,noexec,size=256m",
                        "--user",
                        f"{os.getuid()}:{os.getgid()}",
                        "--env",
                        "HOME=/tmp",
                        "--volume",
                        f"{archive}:/input/image.tar:ro",
                        "--volume",
                        f"{root / 'cache'}:/cache",
                        SCANNER,
                        "image",
                        "--input",
                        "/input/image.tar",
                        "--scanners",
                        "vuln,secret,license",
                        "--license-full",
                        "--list-all-pkgs",
                        "--format",
                        "json",
                        "--cache-dir",
                        "/cache",
                        "--cache-backend",
                        "memory",
                        "--timeout",
                        "15m",
                    ]
                )
            )
            stage = "CANDIDATE_REPORT_INVALID"
            database = json.loads((root / "cache/db/metadata.json").read_text())
            report.update(summarize_candidate(raw, proof, database))
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        AttributeError,
        tarfile.TarError,
        subprocess.SubprocessError,
    ):
        report.update(failure(stage))
    report.update(
        {
            "candidate": args.candidate,
            "architecture": args.architecture,
            "upstream_signature": "not_verified",
            "upstream_provenance": "not_verified",
            "provenance_observation": "registry_digest_and_config_only",
            "upstream_license_approval": "not_granted",
            "release_authorization": "not_granted",
        }
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(
        {"completed_clean": 0, "completed_with_findings": 2}.get(report["execution"], 1)
    )


if __name__ == "__main__":
    main()
