import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from archive import seal, unseal, validate_tree, manifest_files


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.key = self.root / "key"
        self.key.write_bytes(os.urandom(32))
        self.key.chmod(0o600)
        self.data = self.root / "data"
        self.data.mkdir(mode=0o700)
        (self.data / "application.dump").write_bytes(b"sensitive data")
        (self.data / "manifest.json").write_text(
            json.dumps(
                {"schema": "oligospace-recovery/v1", "files": manifest_files(self.data)}
            )
        )

    def test_roundtrip_authenticated_private_and_no_plaintext(self):
        target = self.root / "backup.osbk"
        seal(self.data, target, self.key)
        self.assertNotIn(b"sensitive data", target.read_bytes())
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        restored = self.root / "restored"
        unseal(target, restored, self.key)
        validate_tree(restored)
        self.assertEqual(
            (restored / "application.dump").read_bytes(), b"sensitive data"
        )

    def test_wrong_key_and_corruption_cannot_extract(self):
        target = self.root / "backup.osbk"
        seal(self.data, target, self.key)
        wrong = self.root / "wrong"
        wrong.write_bytes(os.urandom(32))
        wrong.chmod(0o600)
        for key, corrupt in [(wrong, False), (self.key, True)]:
            if corrupt:
                b = bytearray(target.read_bytes())
                b[30] ^= 1
                target.write_bytes(b)
            dest = self.root / "failed"
            with self.assertRaises(ValueError):
                unseal(target, dest, key)
            self.assertFalse(dest.exists())

    def test_incomplete_or_extra_tree_rejected(self):
        (self.data / "application.dump").unlink()
        with self.assertRaises(ValueError):
            validate_tree(self.data)
        (self.data / "application.dump").write_bytes(b"sensitive data")
        (self.data / "extra").write_bytes(b"x")
        with self.assertRaises(ValueError):
            validate_tree(self.data)

    def test_symlink_and_open_key_rejected(self):
        (self.data / "link").symlink_to(self.key)
        with self.assertRaises(ValueError):
            manifest_files(self.data)
        self.key.chmod(0o644)
        with self.assertRaises(ValueError):
            seal(self.data, self.root / "bad", self.key)

    def test_authenticated_missing_member_rejected(self):
        (self.data / "application.dump").unlink()
        with self.assertRaises(ValueError):
            seal(self.data, self.root / "bad", self.key)
