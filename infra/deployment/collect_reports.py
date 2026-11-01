"""Combine qualification descriptors/facts, never publish an image or open a gate."""

import argparse
import hashlib
import json
import math
from pathlib import Path


def compare_payloads(left, right):
    deltas = {}

    def visit(a, b, path):
        if isinstance(a, dict) and isinstance(b, dict) and set(a) == set(b):
            for key in a:
                visit(a[key], b[key], path + "/" + key)
        elif (
            isinstance(a, (int, float))
            and not isinstance(a, bool)
            and isinstance(b, (int, float))
            and not isinstance(b, bool)
        ):
            if (
                not math.isfinite(a)
                or not math.isfinite(b)
                or not math.isclose(a, b, rel_tol=0, abs_tol=1e-6)
            ):
                raise ValueError("scientific_numeric_mismatch")
            deltas[path] = abs(a - b)
        elif type(a) is not type(b) or a != b:
            raise ValueError("scientific_shape_method_unit_mismatch")

    visit(left, right, "payload")
    return {
        "absolute_tolerance": 1e-6,
        "relative_tolerance": 0,
        "max_absolute_delta": max(deltas.values(), default=0),
        "per_fact_delta": deltas,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    reports = {}
    source = None
    for path in args.input.rglob("*-oci-report.json"):
        report = json.loads(path.read_text())
        build = json.loads(path.with_name("qualification-manifest.json").read_text())
        key = (report["role"], report["architecture"])
        if (
            report["status"] != "verified"
            or key in reports
            or build["mode"] != "native_build"
            or build["source"] != report["source"]
        ):
            raise ValueError("invalid_or_non_native_evidence")
        if source is not None and source != report["source"]:
            raise ValueError("mixed_source_revisions")
        source = report["source"]
        reports[key] = report
    expected = {
        (role, arch) for role in ("api", "web", "worker") for arch in ("arm64", "amd64")
    }
    if set(reports) != expected:
        raise ValueError("incomplete_architecture_evidence")
    sciences = [
        json.loads(path.read_text()) for path in args.input.rglob("science.json")
    ]
    if len(sciences) != 2 or {r["architecture"] for r in sciences} != {
        "arm64",
        "amd64",
    }:
        raise ValueError("missing_scientific_execution")
    a, b = sciences
    if (
        any(
            a[key] != b[key]
            for key in ("source", "inputs", "parameters", "tool_version")
        )
        or a["source"] != source
        or a["tool_version"] != "2.6.1"
    ):
        raise ValueError("scientific_provenance_mismatch")
    comparison = compare_payloads(a["payload"], b["payload"])
    (args.output / "scientific-comparison.json").write_text(
        json.dumps({"source": source, "status": "compared", **comparison}, indent=2)
        + "\n"
    )
    indexes = {}
    for role in ("api", "web", "worker"):
        index = {
            "schemaVersion": 2,
            "mediaType": "application/vnd.oci.image.index.v1+json",
            "annotations": {
                "org.opencontainers.image.revision": source,
                "org.oligospace.status": "qualification-only-unpublished",
            },
            "manifests": [
                reports[(role, arch)]["descriptor"] for arch in ("arm64", "amd64")
            ],
        }
        raw = (json.dumps(index, sort_keys=True, separators=(",", ":")) + "\n").encode()
        (args.output / f"{role}-multiarch-index.json").write_bytes(raw)
        indexes[role] = "sha256:" + hashlib.sha256(raw).hexdigest()
    (args.output / "qualification-summary.json").write_text(
        json.dumps(
            {
                "source": source,
                "indexes": indexes,
                "shared_roles": {"migrate": "api", "scheduler": "worker"},
                "release": "blocked",
                "note": "Offline descriptors are not registry artifacts; storage/license/authorization and security/restore gates remain open.",
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
