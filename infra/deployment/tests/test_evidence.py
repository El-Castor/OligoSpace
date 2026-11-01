import importlib.util
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch


class EvidenceTests(unittest.TestCase):
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
