"""Normalize sanitized scanner receipts without interpreting reachability or fixes.

Inputs must be public sanitized reports, never raw Trivy/secret reports. Unknown
metadata is represented by null. Output ordering and hashes are deterministic.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re


PUBLIC_FIELDS = (
    "severity",
    "package",
    "installed_version",
    "fixed_version",
    "origin",
    "cvss",
    "severity_source",
    "data_source",
    "primary_url",
    "package_source",
    "layer",
    "package_path",
)
IDENTITY_FIELDS = (
    "source",
    "architecture",
    "application_digest",
    "config_digest",
    "archive_sha256",
    "scanner",
    "vulnerability_database",
)


def public_metadata(value):
    """Exclude unexpected secret-shaped fields even inside public metadata."""
    if isinstance(value, dict):
        return {
            k: public_metadata(v)
            for k, v in sorted(value.items())
            if not re.search(r"secret|token|password|credential|match", k, re.I)
        }
    if isinstance(value, list):
        return [public_metadata(v) for v in value]
    return value


def build_inventory(paths):
    """Return advisory groups and independent per-artifact occurrence counts."""
    inputs, artifacts, annotations = [], [], []
    grouped = defaultdict(list)
    for path in sorted(map(Path, paths), key=str):
        payload = path.read_bytes()
        receipt = json.loads(payload)
        inputs.append(
            {"path": str(path), "sha256": hashlib.sha256(payload).hexdigest()}
        )
        review = receipt.get("debian_review", {})
        for group in review.get("groups", []):
            annotations.append(
                {
                    "id": group.get("cve"),
                    "checked_on": review.get("checked_on"),
                    "evidence_path": str(path),
                    "status": "dated_annotation_not_current_fix",
                    **{
                        k: group.get(k)
                        for k in (
                            "source_package",
                            "source_version",
                            "tracker_url",
                            "trixie_status",
                            "trixie_fixed_version",
                            "unstable_fixed_version",
                            "trixie_annotation",
                        )
                    },
                }
            )
        reports = receipt.get("reports")
        if reports is None:
            reports = (
                {str(i): r for i, r in enumerate(receipt["scans"])}
                if "scans" in receipt
                else {"scan": receipt}
            )
        for report_path, report in sorted(reports.items()):
            if not isinstance(report, dict) or "execution" not in report:
                continue
            if not any(k in report for k in ("vulnerabilities", "scanner", "gate")):
                continue
            identity = {k: report.get(k) for k in IDENTITY_FIELDS}
            role_match = re.search(
                r"(?:qualification-(?:amd64|arm64)-|historical-secret-triage/)(api|worker|web)(?:/|$)",
                report_path,
            )
            artifact_id = f"{path}::{report_path}"
            rows = report.get("vulnerabilities")
            completed = report.get("execution") in (
                "completed_clean",
                "completed_with_findings",
            ) and isinstance(rows, list)
            assessment = "not_verified"
            if completed:
                assessment = (
                    "findings" if rows or report.get("secret_findings") else "clean"
                )
            artifact = {
                "artifact_id": artifact_id,
                "report_path": report_path,
                **identity,
                "role": role_match[1] if role_match else report.get("role"),
                "execution": report.get("execution"),
                "assessment": assessment,
                "rule_id": report.get("rule_id"),
                "binary_occurrences": len(rows) if isinstance(rows, list) else None,
                "distinct_advisories": len({r["id"] for r in rows})
                if isinstance(rows, list)
                else None,
                "severity_counts": dict(
                    sorted(Counter(r.get("severity", "UNKNOWN") for r in rows).items())
                )
                if isinstance(rows, list)
                else None,
            }
            artifacts.append(artifact)
            for row in rows or []:
                grouped[row["id"]].append(
                    {
                        "artifact_id": artifact_id,
                        "role": artifact["role"],
                        **identity,
                        **{k: public_metadata(row.get(k)) for k in PUBLIC_FIELDS},
                        "usage": "not_established",
                        "exploitability": "not_established",
                    }
                )
    return {
        "schema": "deploy03-inventory/v1",
        "inputs": inputs,
        "distinct_advisories": len(grouped),
        "binary_occurrences": sum(len(v) for v in grouped.values()),
        "artifacts": artifacts,
        "advisories": [{"id": k, "occurrences": grouped[k]} for k in sorted(grouped)],
        "dated_debian_annotations": annotations,
        "unknown_metadata": "null means not retained or not established; never zero or inapplicable",
        "raw_secret_fields_retained": False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = build_inventory(args.inputs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
