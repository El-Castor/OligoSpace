"""Inventory counts must preserve image and package distinctions."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


class InventoryTests(unittest.TestCase):
    def build(self, evidence):
        spec = importlib.util.spec_from_file_location(
            "inventory", Path(__file__).parents[1] / "inventory.py"
        )
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(evidence))
            return module.build_inventory([path])

    def test_distinguishes_advisories_packages_and_images(self):
        finding = dict(
            id="CVE-2026-1", severity="HIGH", package="a", installed_version="1"
        )
        reports = {}
        for role in ("api", "worker"):
            for arch in ("amd64", "arm64"):
                reports[f"qualification-{arch}-{role}/oci/scan.json"] = dict(
                    execution="completed_with_findings",
                    architecture=arch,
                    source="source",
                    application_digest=role + arch,
                    vulnerabilities=[
                        finding,
                        {**finding, "package": "b", "installed_version": "2"},
                    ],
                )
        result = self.build(dict(reports=reports))
        self.assertEqual(result["distinct_advisories"], 1)
        self.assertEqual(result["binary_occurrences"], 8)
        self.assertEqual(len(result["artifacts"]), 4)
        self.assertEqual(result["advisories"][0]["occurrences"][0]["cvss"], None)
        self.assertEqual(
            {o["installed_version"] for o in result["advisories"][0]["occurrences"]},
            {"1", "2"},
        )

    def test_failure_is_never_clean_and_unknown_fields_are_not_copied(self):
        result = self.build(
            dict(
                execution="technical_failure",
                gate="passed",
                secret_observations=[{"Match": "PRIVATE"}],
            )
        )
        self.assertEqual(result["artifacts"][0]["assessment"], "not_verified")
        self.assertNotIn("PRIVATE", json.dumps(result))

    def test_all_severities_and_enhanced_public_fields_survive(self):
        rows = [
            dict(
                id=f"CVE-2026-{i}",
                severity=s,
                package="a",
                cvss={"nvd": {"V3Score": 7.5}},
                severity_source="nvd",
                layer={"digest": "sha256:a"},
            )
            for i, s in enumerate(("UNKNOWN", "LOW", "MEDIUM", "HIGH", "CRITICAL"))
        ]
        result = self.build(
            dict(execution="completed_with_findings", vulnerabilities=rows)
        )
        self.assertEqual(result["distinct_advisories"], 5)
        self.assertEqual(
            result["advisories"][0]["occurrences"][0]["cvss"]["nvd"]["V3Score"], 7.5
        )

    def test_historical_native_high_scope_is_nine_not_176(self):
        root = Path(__file__).resolve().parents[3]
        evidence = json.loads(
            (
                root / "infra/deployment/evidence/security-98a3250-remediation.json"
            ).read_text()
        )
        result = self.build(evidence)
        native = [
            a
            for a in result["artifacts"]
            if a["role"] in ("api", "worker")
            and a["report_path"].startswith("qualification-")
        ]
        self.assertEqual(len(native), 4)
        self.assertEqual(sum(a["severity_counts"]["HIGH"] for a in native), 176)
        identifiers = {a["artifact_id"] for a in native}
        highs = [
            g
            for g in result["advisories"]
            if any(
                o["artifact_id"] in identifiers and o["severity"] == "HIGH"
                for o in g["occurrences"]
            )
        ]
        self.assertEqual(len(highs), 9)


if __name__ == "__main__":
    unittest.main()
