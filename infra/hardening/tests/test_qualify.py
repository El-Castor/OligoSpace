import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    "qualify", Path(__file__).resolve().parents[1] / "qualify.py"
)
qualify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualify)


class ProbeEvidenceTests(unittest.TestCase):
    def test_probe_identity_and_outcome_must_agree(self):
        value = {
            "role": "worker",
            "actual_architecture": "arm64",
            "status": "passed",
            "reason_codes": [],
        }
        self.assertTrue(qualify.valid_probe(value, "worker", "arm64"))
        self.assertFalse(qualify.valid_probe(value, "api", "arm64"))
        self.assertFalse(qualify.valid_probe(value, "worker", "amd64"))
        self.assertFalse(
            qualify.valid_probe(
                {**value, "reason_codes": ["failed"]}, "worker", "arm64"
            )
        )
        self.assertFalse(qualify.valid_probe({}, "worker", "arm64"))


if __name__ == "__main__":
    unittest.main()
