"""Evidence collection contracts for the real disposable recovery harness."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
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

    def test_build_failure_diagnostic_contains_fixed_labels_only(self):
        failed = subprocess.CompletedProcess(
            ["docker", "compose", "build", "api"],
            1,
            stdout=b"private-credential Unable to locate package private-package",
            stderr=b"failed to solve",
        )
        with patch.object(qualification.subprocess, "run", return_value=failed):
            with self.assertRaises(qualification.QualificationError) as error:
                qualification.execute(failed.args)
        self.assertEqual(
            error.exception.diagnostic,
            {"command_phase": "build", "categories": ["build", "apt_index"]},
        )
        self.assertNotIn("private", str(error.exception))
        self.assertNotIn("private", json.dumps(error.exception.diagnostic))

    def test_consistent_object_omission_requires_cross_store_refusal(self):
        import archive
        from recovery import Recovery
        from s3 import validate_export

        with tempfile.TemporaryDirectory() as directory:
            tree = Path(directory)
            (tree / "objects").mkdir()
            payload = tree / "objects/0.bin"
            payload.write_bytes(b"synthetic")
            reference = {
                "object_key": "quarantine/evidence.txt",
                "sha256": archive.digest(payload),
                "size_bytes": 9,
                "content_type": "text/plain",
            }
            manifest = {
                "schema": "oligospace-recovery/v1",
                "attachment_references": [reference],
                "buckets": [
                    {
                        "bucket": "recovery-evidence",
                        "objects": [
                            {
                                "key": reference["object_key"],
                                "file": "objects/0.bin",
                                "sha256": reference["sha256"],
                                "size": 9,
                                "content_type": "text/plain",
                                "metadata": {},
                                "tags": {},
                            }
                        ],
                    }
                ],
                "files": archive.manifest_files(tree),
            }
            (tree / "manifest.json").write_text(json.dumps(manifest))
            qualification.omit_referenced_object(tree)
            incomplete = archive.validate_tree(tree)
            validate_export(incomplete["buckets"], tree)
            self.assertEqual(incomplete["attachment_references"], [reference])
            self.assertEqual(incomplete["buckets"][0]["objects"], [])
            checker = object.__new__(Recovery)
            checker.config = {"buckets": ["recovery-evidence"]}
            with self.assertRaisesRegex(
                ValueError, "attachment_object_integrity_failed"
            ):
                checker._validate_attachment_records(
                    incomplete["attachment_references"], incomplete["buckets"]
                )


if __name__ == "__main__":
    unittest.main()
