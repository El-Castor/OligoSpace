"""Run an actual vulnerability/secret scan, retain only a sanitized summary.

Exit 0 means collection succeeded, NOT vulnerability acceptance. Findings block
the release gate. Raw secret matches never enter uploaded reports or logs.
"""

import argparse
from collections import Counter
import json
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

SCANNER = "aquasec/trivy@sha256:790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c"


def summarize(raw):
    severity = Counter()
    identifiers = set()
    secret_count = 0
    for result in raw.get("Results", []):
        secret_count += len(result.get("Secrets", []))
        for vulnerability in result.get("Vulnerabilities", []):
            severity[vulnerability.get("Severity", "UNKNOWN")] += 1
            identifiers.add(vulnerability.get("VulnerabilityID", "unknown"))
    return {
        "execution": "succeeded",
        "gate": "failed" if secret_count or severity else "passed",
        "secret_findings": secret_count,
        "vulnerabilities_by_severity": dict(severity),
        "vulnerability_ids": sorted(identifiers),
        "scanner": SCANNER,
        "raw_matches_retained": False,
        "risk_acceptance": "not_granted",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    docker = ["docker", "--context", args.context]
    endpoint = json.loads(
        subprocess.check_output(docker + ["context", "inspect", args.context])
    )[0]["Endpoints"]["docker"]["Host"]
    if not endpoint.startswith("unix://") or os.environ.get("DOCKER_HOST"):
        raise ValueError("local_engine_required")
    archive = args.archive.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="oligospace-deploy02-scan-") as directory:
        raw_path = Path(directory) / "raw.json"
        result = subprocess.run(
            docker
            + [
                "run",
                "--rm",
                "--user",
                f"{os.getuid()}:{os.getgid()}",
                "--volume",
                f"{archive}:/input/image.tar:ro",
                "--volume",
                f"{directory}:/report",
                SCANNER,
                "image",
                "--input",
                "/input/image.tar",
                "--scanners",
                "vuln,secret",
                "--format",
                "json",
                "--output",
                "/report/raw.json",
                "--cache-dir",
                "/report/cache",
                "--timeout",
                "15m",
            ],
            capture_output=True,
            text=True,
            check=False,
            timeout=1000,
        )
        if result.returncode or not raw_path.exists():
            report = {
                "execution": "blocked",
                "gate": "not_verified",
                "reason": "scanner_execution_failed",
                "scanner": SCANNER,
            }
        else:
            report = summarize(json.loads(raw_path.read_text()))
            database = Path(directory) / "cache/db/metadata.json"
            report["vulnerability_database"] = (
                json.loads(database.read_text())
                if database.exists()
                else {"status": "not_recorded"}
            )
        checksum = hashlib.sha256()
        with archive.open("rb") as artifact:
            for chunk in iter(lambda: artifact.read(1024 * 1024), b""):
                checksum.update(chunk)
        report["archive_sha256"] = checksum.hexdigest()
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    if report["execution"] != "succeeded":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
