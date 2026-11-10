from pathlib import Path
import tempfile
import os
import sys
import unittest
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archive import seal, manifest_files
from retention import transfer, prune


class RetentionTests(unittest.TestCase):
    def test_transfer_checks_bytes_and_retention_keeps_newest(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            key = r / "key"
            key.write_bytes(os.urandom(32))
            key.chmod(0o600)
            tree = r / "tree"
            tree.mkdir()
            (tree / "data").write_bytes(b"x")
            (tree / "manifest.json").write_text(
                json.dumps(
                    {"schema": "oligospace-recovery/v1", "files": manifest_files(tree)}
                )
            )
            src = r / "a.osbk"
            seal(tree, src, key)
            external = r / "external"
            external.mkdir(mode=0o700)
            first = external / "first.osbk"
            transfer(src, first, key)
            second = external / "second.osbk"
            transfer(src, second, key)
            os.utime(first, (1, 1))
            os.utime(second, (2, 2))
            self.assertEqual(
                prune(external, key, keep=1, minimum_age_days=0, apply=False), 1
            )
            self.assertTrue(first.exists())
            self.assertEqual(
                prune(external, key, keep=1, minimum_age_days=0, apply=True), 1
            )
            self.assertFalse(first.exists())
            self.assertTrue(second.exists())

    def test_corrupt_archive_blocks_cleanup_and_zero_keep_refused(self):
        with tempfile.TemporaryDirectory() as d:
            r = Path(d)
            r.chmod(0o700)
            key = r / "key"
            key.write_bytes(os.urandom(32))
            key.chmod(0o600)
            (r / "bad.osbk").write_bytes(b"bad")
            with self.assertRaises(ValueError):
                prune(r, key, keep=1, minimum_age_days=0, apply=True)
            with self.assertRaises(ValueError):
                prune(r, key, keep=0, minimum_age_days=0, apply=True)
            self.assertTrue((r / "bad.osbk").exists())
