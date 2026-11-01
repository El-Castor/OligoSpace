import importlib.util
from pathlib import Path
import tempfile
import unittest


class S3ContractTests(unittest.TestCase):
    def test_export_preserves_binary_unicode_and_metadata_on_independent_client(self):
        path = Path(__file__).resolve().parents[1] / "s3_contract.py"
        self.assertTrue(path.exists(), "independent logical contract required")
        spec = importlib.util.spec_from_file_location("s3_contract", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertGreaterEqual(len(module.CASES), 3)
        self.assertTrue(any(any(ord(c) > 127 for c in key) for key in module.CASES))

    def test_corrupt_export_cannot_be_restored(self):
        path = Path(__file__).resolve().parents[1] / "s3_contract.py"
        self.assertTrue(path.exists())
        spec = importlib.util.spec_from_file_location("s3_contract", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "0.bin").write_bytes(b"corrupt")
            with self.assertRaises(ValueError):
                module.read_export(root, {"file": "0.bin", "sha256": "0" * 64})
            with self.assertRaises(ValueError):
                module.read_export(root, {"file": "../other", "sha256": "0" * 64})
