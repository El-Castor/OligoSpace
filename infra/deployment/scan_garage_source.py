"""Scan the exact upstream Cargo.lock; never equate source with runtime coverage."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

from inspect_garage_binary import COMMIT, LOCK_SHA256
from scan_artifact import SCANNER, failure, summarize_findings
from scan_candidate import inventory, process_failure_diagnostics


def summarize_source(raw, database):
    if not isinstance(raw, dict) or raw.get("SchemaVersion") != 2:
        raise ValueError("invalid_source_report")
    if database.get("Version") != 2 or not all(
        isinstance(database.get(key), str)
        and re.fullmatch(r"[0-9T:Z.+-]+", database[key])
        for key in ("UpdatedAt", "NextUpdate", "DownloadedAt")
    ):
        raise ValueError("database_metadata_missing")
    report = summarize_findings(raw)
    report["package_inventory"] = inventory(raw)
    count = sum(
        len(result.get("Packages", []))
        for result in raw.get("Results", [])
        if result.get("Type") == "cargo"
    )
    report.update(
        source_cargo_packages_observed=count,
        runtime_dependency_coverage="not_verified",
        source_to_binary_provenance="not_verified",
        vulnerability_database=database,
    )
    if count == 0:
        report["coverage_rule_id"] = "GARAGE_SOURCE_PACKAGE_COVERAGE_MISSING"
        if report["gate"] != "failed":
            report.update(execution="technical_failure", gate="not_verified")
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lockfile", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = failure("GARAGE_SOURCE_SCAN_NOT_EXECUTED", "not_executed")
    stage = "GARAGE_SOURCE_IDENTITY_FAILED"
    try:
        if args.lockfile.stat().st_size > 2 * 1024 * 1024:
            raise ValueError("source_size_limit")
        content = args.lockfile.read_bytes()
        if hashlib.sha256(content).hexdigest() != LOCK_SHA256:
            raise ValueError("source_lock_digest_mismatch")
        if os.environ.get("DOCKER_HOST") or os.environ.get("DOCKER_CONTEXT"):
            raise ValueError("local_context_required")
        endpoint = json.loads(
            subprocess.check_output(
                ["docker", "context", "inspect"],
                stderr=subprocess.PIPE,
                timeout=30,
            )
        )[0]["Endpoints"]["docker"]["Host"]
        if not endpoint.startswith("unix://"):
            raise ValueError("local_context_required")
        with tempfile.TemporaryDirectory(
            prefix="oligospace-garage-source-"
        ) as directory:
            root = Path(directory)
            source = root / "source"
            source.mkdir(mode=0o700)
            (source / "Cargo.lock").write_bytes(content)
            (root / "cache").mkdir(mode=0o700)
            stage = "GARAGE_SOURCE_SCANNER_FAILED"
            raw = subprocess.check_output(
                [
                    "docker",
                    "run",
                    "--rm",
                    "--cap-drop=ALL",
                    "--security-opt=no-new-privileges",
                    "--read-only",
                    "--tmpfs",
                    "/tmp:rw,nosuid,nodev,noexec,size=2g",
                    "--user",
                    f"{os.getuid()}:{os.getgid()}",
                    "--env",
                    "HOME=/tmp",
                    "--volume",
                    f"{source}:/source:ro",
                    "--volume",
                    f"{root / 'cache'}:/cache",
                    SCANNER,
                    "filesystem",
                    "--scanners",
                    "vuln,secret",
                    "--list-all-pkgs",
                    "--format",
                    "json",
                    "--cache-dir",
                    "/cache",
                    "--cache-backend",
                    "memory",
                    "--timeout",
                    "15m",
                    "/source",
                ],
                stderr=subprocess.PIPE,
                timeout=1000,
            )
            stage = "GARAGE_SOURCE_REPORT_INVALID"
            metadata = json.loads((root / "cache/db/metadata.json").read_text())
            report = summarize_source(
                json.loads(raw),
                {
                    key: metadata[key]
                    for key in (
                        "Version",
                        "UpdatedAt",
                        "NextUpdate",
                        "DownloadedAt",
                    )
                },
            )
    except subprocess.CalledProcessError as error:
        report = {**failure(stage), **process_failure_diagnostics(error)}
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        subprocess.SubprocessError,
    ):
        report = failure(stage)
    report.update(
        source_commit=COMMIT,
        source_lock_sha256=LOCK_SHA256,
        artifact_kind="source_lockfile_only",
        runtime_dependency_coverage="not_verified",
        release_authorization="not_granted",
        raw_matches_retained=False,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(
        {"completed_clean": 0, "completed_with_findings": 2}.get(report["execution"], 1)
    )


if __name__ == "__main__":
    main()
