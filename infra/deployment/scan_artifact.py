"""Run Trivy against a verified OCI directory; persist sanitized evidence only."""

import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import tarfile
import tempfile

from scan_layout import prepare_layout

SCANNER = "aquasec/trivy@sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c"


def failure_diagnostics(message, exit_code):
    categories = (
        "archive",
        "cache",
        "certificate",
        "connection",
        "database",
        "access denied",
        "invalid",
        "manifest",
        "no such file",
        "oci",
        "permission denied",
        "platform",
        "timeout",
        "unauthorized",
        "unsupported",
    )
    return {
        "exit_code": exit_code,
        "error_categories": [c for c in categories if c in message.lower()],
    }


def failure(rule, state="technical_failure"):
    return {
        "execution": state,
        "gate": "not_verified",
        "rule_id": rule,
        "scanner": SCANNER,
        "raw_matches_retained": False,
    }


def safe_field(value):
    if (
        not isinstance(value, str)
        or len(value) > 160
        or not re.fullmatch(r"[A-Za-z0-9.+_:~@/() -]*", value)
    ):
        raise ValueError("invalid_public_field")
    return value


def summarize(raw, proof, database):
    if (
        not isinstance(raw, dict)
        or raw.get("SchemaVersion") != 2
        or raw.get("ArtifactType") != "container_image"
    ):
        raise ValueError("invalid_report_schema")
    metadata = raw.get("Metadata", {})
    if (
        not isinstance(metadata, dict)
        or metadata.get("ImageID") != proof["config_digest"]
    ):
        raise ValueError("report_identity_mismatch")
    config = metadata.get("ImageConfig", {})
    if (
        not isinstance(config, dict)
        or config.get("architecture") != proof["architecture"]
        or config.get("os") != "linux"
    ):
        raise ValueError("report_platform_mismatch")
    operating_system = metadata.get("OS", {})
    if (
        not isinstance(operating_system, dict)
        or operating_system.get("Family") not in ("debian", "alpine")
        or not operating_system.get("Name")
    ):
        raise ValueError("os_coverage_missing")
    if (
        not isinstance(database, dict)
        or database.get("Version") != 2
        or not all(
            isinstance(database.get(k), str)
            and re.fullmatch(r"[0-9T:Z.+-]+", database[k])
            for k in ("UpdatedAt", "NextUpdate", "DownloadedAt")
        )
    ):
        raise ValueError("database_metadata_missing")
    results = raw.get("Results", [])
    if not isinstance(results, list):
        raise ValueError("invalid_results")
    severity = Counter()
    findings = []
    secret_count = 0
    for result in results:
        if not isinstance(result, dict):
            raise ValueError("invalid_result")
        secrets = result.get("Secrets", [])
        vulnerabilities = result.get("Vulnerabilities", [])
        if not isinstance(secrets, list) or not isinstance(vulnerabilities, list):
            raise ValueError("invalid_findings")
        if any(not isinstance(secret, dict) for secret in secrets):
            raise ValueError("invalid_secrets")
        secret_count += len(secrets)
        for vulnerability in vulnerabilities:
            if not isinstance(vulnerability, dict):
                raise ValueError("invalid_vulnerability")
            identifier = vulnerability.get("VulnerabilityID", "")
            level = vulnerability.get("Severity", "UNKNOWN")
            if not re.fullmatch(
                r"(?:CVE-[0-9]{4}-[0-9]+|GHSA-[a-z0-9-]+)", identifier
            ) or level not in ("UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"):
                raise ValueError("invalid_public_vulnerability")
            severity[level] += 1
            findings.append(
                {
                    "id": identifier,
                    "severity": level,
                    "package": safe_field(vulnerability.get("PkgName", "")),
                    "installed_version": safe_field(
                        vulnerability.get("InstalledVersion", "")
                    ),
                    "fixed_version": safe_field(vulnerability.get("FixedVersion", "")),
                }
            )
    blocked = bool(secret_count or findings)
    return {
        "execution": "completed_with_findings" if blocked else "completed_clean",
        "gate": "failed" if blocked else "passed",
        "secret_findings": secret_count,
        "vulnerabilities_by_severity": dict(severity),
        "vulnerability_ids": sorted({f["id"] for f in findings}),
        "vulnerabilities": findings,
        "scanner": SCANNER,
        "raw_matches_retained": False,
        "risk_acceptance": "not_granted",
        "vulnerability_database": {
            k: database[k]
            for k in ("Version", "UpdatedAt", "NextUpdate", "DownloadedAt")
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--architecture", choices=("arm64", "amd64"), required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    report = failure("SCAN_NOT_EXECUTED", "not_executed")
    proof = {}
    container_attempted = False
    stage = "SCAN_INPUT_INVALID"
    try:
        with tempfile.TemporaryDirectory(
            prefix="oligospace-deploy02-scan-"
        ) as directory:
            root = Path(directory)
            proof = prepare_layout(
                args.archive, root / "layout", args.architecture, args.source
            )
            stage = "SCAN_LOCAL_ENGINE_REQUIRED"
            docker = ["docker", "--context", args.context]
            endpoint = json.loads(
                subprocess.check_output(
                    docker + ["context", "inspect", args.context],
                    stderr=subprocess.PIPE,
                    timeout=30,
                )
            )[0]["Endpoints"]["docker"]["Host"]
            if not endpoint.startswith("unix://") or os.environ.get("DOCKER_HOST"):
                raise ValueError("local_engine_required")
            stage = "SCAN_CACHE_PERMISSIONS"
            (root / "cache").mkdir(mode=0o700)
            stage = "SCAN_CONTAINER_FAILED"
            container_attempted = True
            result = subprocess.run(
                docker
                + [
                    "run",
                    "--rm",
                    "--user",
                    f"{os.getuid()}:{os.getgid()}",
                    "--env",
                    "HOME=/tmp",
                    "--volume",
                    f"{root / 'layout'}:/input/layout:ro",
                    "--volume",
                    f"{root / 'cache'}:/cache",
                    SCANNER,
                    "image",
                    "--input",
                    "/input/layout@" + proof["descriptor"]["digest"],
                    "--scanners",
                    "vuln,secret",
                    "--format",
                    "json",
                    "--cache-dir",
                    "/cache",
                    "--cache-backend",
                    "memory",
                    "--timeout",
                    "15m",
                ],
                capture_output=True,
                text=True,
                check=False,
                timeout=1000,
            )
            if result.returncode:
                message = result.stderr.lower()
                if "permission denied" in message or "access denied" in message:
                    stage = "SCAN_CONTAINER_PERMISSIONS"
                elif "database" in message or "db error" in message:
                    stage = "SCAN_DATABASE_FAILED"
                elif "oci" in message or "manifest" in message:
                    stage = "SCAN_LAYOUT_REJECTED"
                report = failure(stage)
                report.update(failure_diagnostics(result.stderr, result.returncode))
            else:
                stage = "SCAN_DATABASE_METADATA_INVALID"
                database = json.loads((root / "cache/db/metadata.json").read_text())
                stage = "SCAN_REPORT_INVALID"
                report = summarize(json.loads(result.stdout), proof, database)
    except (
        tarfile.TarError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        subprocess.SubprocessError,
    ):
        report = failure(
            stage, "technical_failure" if container_attempted else "not_executed"
        )
    report.update(
        {
            k: proof[k]
            for k in (
                "archive_sha256",
                "source",
                "architecture",
                "config_digest",
                "view_index_sha256",
            )
            if k in proof
        }
    )
    if proof:
        report["application_digest"] = proof["descriptor"]["digest"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(
        {"completed_clean": 0, "completed_with_findings": 2}.get(report["execution"], 1)
    )


if __name__ == "__main__":
    main()
