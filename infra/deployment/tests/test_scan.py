import importlib.util
import json
from pathlib import Path
import sys
import unittest
import subprocess
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location(
    "scan_artifact", Path(__file__).resolve().parents[1] / "scan_artifact.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PROOF = {"config_digest": "sha256:" + "a" * 64, "architecture": "arm64"}
DB = {
    "Version": 2,
    **{k: "2026-11-02T00:00:00Z" for k in ("UpdatedAt", "NextUpdate", "DownloadedAt")},
}


def fixture():
    return {
        "SchemaVersion": 2,
        "ArtifactType": "container_image",
        "Metadata": {
            "ImageID": PROOF["config_digest"],
            "ImageConfig": {"architecture": "arm64", "os": "linux"},
            "OS": {"Family": "debian", "Name": "12"},
        },
    }


class ScanTests(unittest.TestCase):
    def test_valid_multiple_fixed_versions_remain_blocking_findings(self):
        raw = fixture()
        raw["Results"] = [
            {
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2026-1234",
                        "Severity": "HIGH",
                        "PkgName": "synthetic-package",
                        "InstalledVersion": "1.0",
                        "FixedVersion": "1.2.3, 2.3.4",
                    }
                ]
            }
        ]
        report = module.summarize(raw, PROOF, DB)
        self.assertEqual(report["execution"], "completed_with_findings")
        self.assertEqual(report["gate"], "failed")
        self.assertEqual(report["vulnerabilities"][0]["fixed_version"], "1.2.3, 2.3.4")

    def test_validation_rule_identifies_structure_without_error_payload(self):
        self.assertEqual(
            module.validation_rule(
                "SCAN_REPORT_INVALID", ValueError("report_platform_mismatch")
            ),
            "SCAN_REPORT_PLATFORM_MISMATCH",
        )
        self.assertEqual(
            module.validation_rule(
                "SCAN_REPORT_INVALID", ValueError("sensitive-private-error")
            ),
            "SCAN_REPORT_INVALID",
        )

    def test_invalid_input_reports_scan_not_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "invalid.tar"
            archive.write_bytes(b"not-an-oci-archive")
            output = root / "scan.json"
            script = Path(__file__).resolve().parents[1] / "scan_artifact.py"
            process = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--context",
                    "synthetic",
                    "--archive",
                    str(archive),
                    "--source",
                    "a" * 40,
                    "--architecture",
                    "arm64",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(process.returncode, 0)
            report = json.loads(output.read_text())
            self.assertEqual(report["execution"], "not_executed")
            self.assertEqual(report["gate"], "not_verified")

    def test_failure_diagnostics_expose_only_fixed_categories(self):
        report = module.failure_diagnostics(
            "private-match failed database archive permission denied", 1
        )
        self.assertEqual(
            report["error_categories"], ["archive", "database", "permission denied"]
        )
        self.assertNotIn("private-match", json.dumps(report))

    def test_secret_matches_never_enter_sanitized_reports(self):
        raw = fixture()
        raw["Results"] = [
            {
                "Secrets": [{"Match": "sensitive-test-value", "Code": "private"}],
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2026-1234",
                        "Severity": "HIGH",
                        "PkgName": "openssl",
                        "InstalledVersion": "1.0",
                        "FixedVersion": "2.0",
                        "PrimaryURL": "private-url",
                    }
                ],
            }
        ]
        report = module.summarize(raw, PROOF, DB)
        for secret in ("sensitive-test-value", "private", "private-url"):
            self.assertNotIn(secret, json.dumps(report))
        self.assertEqual(report["secret_findings"], 1)
        self.assertEqual(report["execution"], "completed_with_findings")
        self.assertEqual(report["gate"], "failed")

    def test_omitted_results_is_valid_clean_report(self):
        self.assertEqual(
            module.summarize(fixture(), PROOF, DB)["execution"], "completed_clean"
        )

    def test_malformed_reports_fail_closed(self):
        candidates = [
            {},
            [],
            {**fixture(), "Results": {}},
            {**fixture(), "Results": [None]},
            {**fixture(), "Results": [{"Secrets": None}]},
            {**fixture(), "Metadata": {}},
            {
                **fixture(),
                "Results": [
                    {"Vulnerabilities": [{"VulnerabilityID": "private-value"}]}
                ],
            },
        ]
        for raw in candidates:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                module.summarize(raw, PROOF, DB)
        for database in ({}, None):
            with self.assertRaises(ValueError):
                module.summarize(fixture(), PROOF, database)
        raw = fixture()
        raw["Metadata"]["ImageConfig"]["architecture"] = "amd64"
        with self.assertRaises(ValueError):
            module.summarize(raw, PROOF, DB)
        raw = fixture()
        raw["Metadata"].pop("OS")
        with self.assertRaises(ValueError):
            module.summarize(raw, PROOF, DB)
