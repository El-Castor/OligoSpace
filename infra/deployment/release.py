"""Validate a non-secret release-evidence manifest; never deploy or publish."""

from __future__ import annotations

import json
import re
import sys

GATES = (
    "storage",
    "tls_oidc_mfa",
    "rls",
    "threat_model",
    "scans",
    "restore",
    "capacity",
    "incident",
    "private_network",
)


def blockers(manifest: dict) -> list[str]:
    failed = []
    if not re.fullmatch(r"[a-f0-9]{40}", str(manifest.get("source", ""))):
        failed.append("source")
    images = manifest.get("images", {})
    registry = manifest.get("authorized_registry", "")
    for role in ("api", "web", "worker", "migrate", "scheduler"):
        reference = images.get(role, "")
        if (
            not registry
            or not reference.startswith(registry.rstrip("/") + "/")
            or not re.fullmatch(r"[^@\s]+@sha256:[a-f0-9]{64}", reference)
        ):
            failed.append("image_" + role)
    if images.get("api") != images.get("migrate"):
        failed.append("migration_image")
    if images.get("worker") != images.get("scheduler"):
        failed.append("scheduler_image")
    for gate in GATES:
        evidence = manifest.get(gate, {})
        # This foundation does NOT implement waivers. No implicit acceptance.
        if evidence.get("status") != "passed" or not evidence.get("evidence"):
            failed.append(gate)
    architectures = manifest.get("architectures", {})
    for arch in ("arm64", "amd64"):
        evidence = architectures.get(arch, {})
        if (
            evidence.get("mode") != "native"
            or evidence.get("source") != manifest.get("source")
            or evidence.get("tests") != "passed"
            or evidence.get("primer3_version") != "2.6.1"
            or not evidence.get("report")
            or not evidence.get("scientific_comparison")
        ):
            failed.append("native_architectures")
            break
    return sorted(set(failed))


def main() -> int:
    try:
        failures = blockers(json.load(sys.stdin))
    except (ValueError, AttributeError, TypeError):
        failures = ["invalid_manifest"]
    print(
        json.dumps(
            {
                "release": "blocked"
                if failures
                else "evidence_complete_pending_approval",
                "blockers": failures,
            }
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
