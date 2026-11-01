import importlib.util
import json
from pathlib import Path
import unittest


class ScanTests(unittest.TestCase):
    def test_secret_matches_never_enter_sanitized_reports(self):
        path = Path(__file__).resolve().parents[1] / "scan_artifact.py"
        self.assertTrue(path.exists())
        spec = importlib.util.spec_from_file_location("scan_artifact", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        raw = {
            "Results": [
                {
                    "Secrets": [{"Match": "sensitive-test-only-value", "StartLine": 3}],
                    "Vulnerabilities": [
                        {"VulnerabilityID": "CVE-synthetic", "Severity": "HIGH"}
                    ],
                }
            ]
        }
        report = module.summarize(raw)
        self.assertNotIn("sensitive-test-only-value", json.dumps(report))
        self.assertEqual(report["secret_findings"], 1)
        self.assertEqual(report["gate"], "failed")
