import importlib.util
import json
import hashlib
from pathlib import Path
import unittest


class InventoryTests(unittest.TestCase):
    def test_manifest_digest_and_platforms_are_verified_not_assumed(self):
        path = Path(__file__).resolve().parents[1] / "image_inventory.py"
        self.assertTrue(path.exists())
        spec = importlib.util.spec_from_file_location("image_inventory", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        raw = json.dumps(
            {
                "manifests": [
                    {
                        "digest": "sha256:" + "a" * 64,
                        "platform": {"os": "linux", "architecture": "arm64"},
                    }
                ]
            }
        ).encode()
        digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        record = module.verify_manifest(raw, digest)
        self.assertIn("arm64", record["platforms"])
        self.assertNotIn("amd64", record["platforms"])
        with self.assertRaises(ValueError):
            module.verify_manifest(raw + b" ", digest)
        with self.assertRaises(ValueError):
            module.reference_parts("minio/minio:latest")
