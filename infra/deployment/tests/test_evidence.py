import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


class EvidenceTests(unittest.TestCase):
    def module(self):
        path = Path(__file__).resolve().parents[1] / "evidence.py"
        spec = importlib.util.spec_from_file_location("evidence", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_access_identifier_and_secret_value_are_separate_failed_rules(self):
        module = self.module()
        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                [], 0, b"synthetic-access-id", b"synthetic-secret"
            ),
        ):
            report = module.credential_log_report(
                ["docker"], "synthetic", ["synthetic-access-id"], ["synthetic-secret"]
            )
        self.assertEqual(report["status"], "failed")
        self.assertEqual(report["stdout_rule_ids"], ["LOG_ACCESS_IDENTIFIER_PRESENT"])
        self.assertEqual(report["stderr_rule_ids"], ["LOG_SECRET_VALUE_PRESENT"])
        import json

        self.assertNotIn("synthetic-access-id", json.dumps(report))
        self.assertNotIn("synthetic-secret", json.dumps(report))

    def test_log_retrieval_failure_is_not_a_credential_disclosure(self):
        module = self.module()
        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                [], 1, b"", b"untrusted-private-error"
            ),
        ):
            report = module.credential_log_report(
                ["docker"], "synthetic", ["id"], ["secret"]
            )
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["rule_ids"], ["LOG_RETRIEVAL_FAILED"])
        self.assertNotIn("untrusted-private-error", str(report))

    def test_controller_exception_is_distinct_and_never_discloses_exception_text(self):
        module = self.module()
        with patch("subprocess.run", side_effect=OSError("private-error-value")):
            report = module.credential_log_report(
                ["docker"], "synthetic", ["id"], ["secret"]
            )
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["rule_ids"], ["LOG_CONTROLLER_EXECUTION_FAILED"])
        self.assertNotIn("private-error-value", str(report))

    def test_missing_credential_inventory_cannot_pass(self):
        module = self.module()
        report = module.credential_log_report(["docker"], "synthetic", [], [])
        self.assertEqual(report["status"], "blocked")
        self.assertEqual(report["rule_ids"], ["LOG_CONTROLLER_INPUT_INVALID"])

    def test_clear_logs_pass_both_streams_without_printing_payload(self):
        module = self.module()
        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, b"ordinary", b"warning"),
        ):
            report = module.credential_log_report(
                ["docker"], "synthetic", ["id"], ["secret"]
            )
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["rule_ids"], ["LOG_NO_CREDENTIAL_MATCH"])

    def test_secret_only_on_stderr_cannot_pass_log_gate(self):
        path = Path(__file__).resolve().parents[1] / "evidence.py"
        self.assertTrue(path.exists(), "both log streams must be checked")
        spec = importlib.util.spec_from_file_location("evidence", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch(
            "subprocess.run",
            return_value=subprocess.CompletedProcess(
                [], 0, "ordinary log", "sensitive-test-value"
            ),
        ):
            self.assertFalse(
                module.credentials_absent_from_logs(
                    ["docker"], "disposable", ["sensitive-test-value"]
                )
            )
