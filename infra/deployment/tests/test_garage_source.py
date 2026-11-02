from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scan_garage_source import summarize_source

DB = {
    "Version": 2,
    **{
        key: "2026-11-02T00:00:00Z"
        for key in ("UpdatedAt", "NextUpdate", "DownloadedAt")
    },
}


class SourceCoverageTests(unittest.TestCase):
    def test_absent_cargo_inventory_never_means_clean(self):
        report = summarize_source({"SchemaVersion": 2, "Results": []}, DB)
        self.assertEqual(report["gate"], "not_verified")
        self.assertEqual(report["runtime_dependency_coverage"], "not_verified")

    def test_source_findings_block_without_claiming_runtime_membership(self):
        raw = {
            "SchemaVersion": 2,
            "Results": [
                {
                    "Type": "cargo",
                    "Packages": [{"Name": "public-crate", "Version": "1.0"}],
                    "Secrets": [{"Match": "synthetic-private-value"}],
                    "Vulnerabilities": [
                        {
                            "VulnerabilityID": "RUSTSEC-2026-0001",
                            "Severity": "HIGH",
                            "PkgName": "public-crate",
                            "InstalledVersion": "1.0",
                            "FixedVersion": "1.1",
                        }
                    ],
                }
            ],
        }
        report = summarize_source(raw, DB)
        self.assertEqual(report["gate"], "failed")
        self.assertEqual(report["source_cargo_packages_observed"], 1)
        self.assertNotIn("synthetic-private-value", str(report))
        self.assertEqual(report["source_to_binary_provenance"], "not_verified")
        with self.assertRaises(ValueError):
            summarize_source(raw, {})
