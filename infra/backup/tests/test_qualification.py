"""Evidence collection contracts for the real disposable recovery harness."""

import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location(
    "recovery_qualification", ROOT / "qualify.py"
)
qualification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualification)


class QualificationEvidenceTests(unittest.TestCase):
    def test_successful_log_retrieval_includes_stderr(self):
        # A service leaking on stderr must be visible to the log gate as well.
        actual = qualification.execute(
            [
                sys.executable,
                "-c",
                "import sys; print('stdout'); print('stderr-secret',file=sys.stderr)",
            ],
            merge_stderr=True,
        )
        self.assertIn(b"stdout", actual)
        self.assertIn(b"stderr-secret", actual)

    def test_failed_log_retrieval_never_proves_absence(self):
        with self.assertRaisesRegex(
            qualification.QualificationError, "qualification_command_failed"
        ) as error:
            qualification.execute(
                [
                    sys.executable,
                    "-c",
                    "import sys; print('private-credential',file=sys.stderr); sys.exit(2)",
                ],
                merge_stderr=True,
            )
        self.assertNotIn("private-credential", str(error.exception))

    def test_negative_case_must_actually_fail(self):
        with self.assertRaisesRegex(
            qualification.QualificationError,
            "negative_case_did_not_refuse_corrupt_archive",
        ):
            qualification.expect_failure(lambda: None, "corrupt_archive")

    def test_command_timeout_is_never_successful_empty_output(self):
        with patch.object(
            qualification.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired("operation", 1),
        ):
            with self.assertRaises(subprocess.TimeoutExpired):
                qualification.execute(["irrelevant"], merge_stderr=True)


if __name__ == "__main__":
    unittest.main()
