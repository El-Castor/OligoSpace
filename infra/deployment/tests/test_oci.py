import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest


def archive(path, source="a" * 40, corrupt=False, attest=True):
    files = {"oci-layout": b'{"imageLayoutVersion":"1.0.0"}'}

    def blob(obj, media):
        raw = obj if isinstance(obj, bytes) else json.dumps(obj).encode()
        checksum = hashlib.sha256(raw).hexdigest()
        files["blobs/sha256/" + checksum] = raw
        return {"digest": "sha256:" + checksum, "size": len(raw), "mediaType": media}

    config = blob(
        {
            "architecture": "arm64",
            "os": "linux",
            "config": {
                "User": "1000",
                "Labels": {"org.opencontainers.image.revision": source},
            },
        },
        "application/vnd.oci.image.config.v1+json",
    )
    layer = blob(b"synthetic-layer", "application/vnd.oci.image.layer.v1.tar")
    image = blob(
        {"config": config, "layers": [layer]},
        "application/vnd.oci.image.manifest.v1+json",
    )
    image["platform"] = {"os": "linux", "architecture": "arm64"}
    manifests = [image]
    if attest:
        layers = []
        for predicate in (
            "https://spdx.dev/Document",
            "https://slsa.dev/provenance/v0.2",
        ):
            layers.append(
                blob(
                    {
                        "predicateType": predicate,
                        "subject": [{"digest": {"sha256": image["digest"][7:]}}],
                        "predicate": {},
                    },
                    "application/vnd.in-toto+json",
                )
            )
        manifests.append(
            blob(
                {"config": config, "layers": layers},
                "application/vnd.oci.image.manifest.v1+json",
            )
        )
    files["index.json"] = json.dumps(
        {"schemaVersion": 2, "manifests": manifests}
    ).encode()
    if corrupt:
        files["blobs/sha256/" + layer["digest"][7:]] += b"changed"
    with tarfile.open(path, "w") as tar:
        for name, data in files.items():
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            tar.addfile(entry, io.BytesIO(data))


class OCITests(unittest.TestCase):
    def test_verified_bytes_source_architecture_and_attestations(self):
        path = Path(__file__).resolve().parents[1] / "oci.py"
        self.assertTrue(path.exists())
        spec = importlib.util.spec_from_file_location("oci", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory() as directory:
            tar = Path(directory) / "test.tar"
            archive(tar)
            self.assertEqual(
                module.verify_oci(tar, "arm64", "a" * 40)["status"], "verified"
            )
            with self.assertRaises(ValueError):
                module.verify_oci(tar, "amd64", "a" * 40)
            archive(tar, corrupt=True)
            with self.assertRaises(ValueError):
                module.verify_oci(tar, "arm64", "a" * 40)
            archive(tar, attest=False)
            with self.assertRaises(ValueError):
                module.verify_oci(tar, "arm64", "a" * 40)
