import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from test_oci import archive


def module():
    path = Path(__file__).resolve().parents[1] / "scan_layout.py"
    spec = importlib.util.spec_from_file_location("scan_layout", path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class LayoutTests(unittest.TestCase):
    def test_archive_and_expanded_budgets_are_enforced_before_extraction(self):
        scanner = module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "image.tar"
            archive(source)
            for budget, limit in [
                ("MAX_ARCHIVE_BYTES", 1),
                ("MAX_EXPANDED_BYTES", 100),
                ("MAX_MEMBERS", 1),
            ]:
                with self.subTest(budget=budget), patch.object(scanner, budget, limit):
                    with self.assertRaises(ValueError):
                        scanner.prepare_layout(
                            source, root / "layout", "arm64", "a" * 40
                        )
                    self.assertFalse((root / "layout").exists())

    def test_nested_attestation_first_index_selects_verified_app_without_losing_blobs(
        self,
    ):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "image.oci.tar"
            archive(source)
            with tarfile.open(source) as tar:
                files = {m.name: tar.extractfile(m).read() for m in tar.getmembers()}
            original = json.loads(files["index.json"])
            expected = original["manifests"][0]
            original["manifests"].reverse()
            child = json.dumps(original).encode()
            digest = hashlib.sha256(child).hexdigest()
            files["blobs/sha256/" + digest] = child
            files["index.json"] = json.dumps(
                {
                    "schemaVersion": 2,
                    "manifests": [
                        {
                            "mediaType": "application/vnd.oci.image.index.v1+json",
                            "size": len(child),
                            "digest": "sha256:" + digest,
                        }
                    ],
                }
            ).encode()
            with tarfile.open(source, "w") as tar:
                for name, data in files.items():
                    entry = tarfile.TarInfo(name)
                    entry.size = len(data)
                    tar.addfile(entry, io.BytesIO(data))
            before = source.read_bytes()
            proof = module().prepare_layout(source, root / "layout", "arm64", "a" * 40)
            self.assertEqual(
                json.loads((root / "layout/index.json").read_text())["manifests"],
                [expected],
            )
            self.assertEqual(proof["descriptor"], expected)
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(
                proof["archive_sha256"], hashlib.sha256(before).hexdigest()
            )
            for name, data in files.items():
                if name.startswith("blobs/"):
                    self.assertEqual((root / "layout" / name).read_bytes(), data)
            self.assertEqual((root / "layout").stat().st_mode & 0o777, 0o700)

    def test_corrupt_bytes_and_wrong_identity_are_refused_before_extraction(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "image.tar"
            archive(source, corrupt=True)
            with self.assertRaises(ValueError):
                module().prepare_layout(source, root / "layout", "arm64", "a" * 40)
            self.assertFalse((root / "layout").exists())
            archive(source)
            with self.assertRaises(ValueError):
                module().prepare_layout(source, root / "layout", "amd64", "a" * 40)
            with self.assertRaises(ValueError):
                module().prepare_layout(source, root / "layout", "arm64", "b" * 40)

    def test_links_and_paths_cannot_escape_private_layout(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, link in [
                ("../escape", False),
                ("blobs/sha256/" + "a" * 64, True),
            ]:
                with self.subTest(name=name):
                    source = root / "unsafe.tar"
                    with tarfile.open(source, "w") as tar:
                        entry = tarfile.TarInfo(name)
                        if link:
                            entry.type = tarfile.SYMTYPE
                            entry.linkname = "../../escape"
                        tar.addfile(entry)
                    with self.assertRaises(ValueError):
                        module().prepare_layout(
                            source, root / "layout", "arm64", "a" * 40
                        )
                    self.assertFalse((root / "escape").exists())
                    self.assertFalse((root / "layout").exists())
