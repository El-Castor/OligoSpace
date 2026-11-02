import hashlib
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from inspect_garage_binary import compare, fingerprint, image_fingerprint, release_url


def elf(architecture="amd64", suffix=b""):
    header = bytearray(64)
    header[:6] = b"\x7fELF\x02\x01"
    header[18:20] = {"amd64": 62, "arm64": 183}[architecture].to_bytes(2, "little")
    return bytes(header) + suffix


def tar_bytes(entries):
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w") as tar:
        for name, content, link in entries:
            member = tarfile.TarInfo(name)
            if link:
                member.type = tarfile.SYMTYPE
                member.linkname = link
                tar.addfile(member)
            else:
                member.size = len(content)
                tar.addfile(member, io.BytesIO(content))
    return buffer.getvalue()


class GarageBinaryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def archive(self, layers, tamper=False):
        layer_data = [tar_bytes(layer) for layer in layers]
        config = json.dumps(
            {
                "os": "linux",
                "architecture": "amd64",
                "rootfs": {
                    "type": "layers",
                    "diff_ids": [
                        "sha256:" + hashlib.sha256(data).hexdigest()
                        for data in layer_data
                    ],
                },
            }
        ).encode()
        digest = "sha256:" + hashlib.sha256(config).hexdigest()
        names = [str(index) + "/layer.tar" for index in range(len(layers))]
        manifest = json.dumps([{"Config": "config.json", "Layers": names}]).encode()
        if tamper:
            layer_data[0] += b"tamper"
        entries = [("manifest.json", manifest, None), ("config.json", config, None)]
        entries += [(name, data, None) for name, data in zip(names, layer_data)]
        path = self.root / "image.tar"
        path.write_bytes(tar_bytes(entries))
        return path, digest

    def test_exact_comparison_and_conservative_claims(self):
        data = elf(suffix=b".dep-v0")
        archive, digest = self.archive([[("garage", data, None)]])
        release = self.root / "release"
        release.write_bytes(data)
        report = compare(archive, digest, "amd64", release)
        self.assertTrue(report["binary_match"])
        self.assertFalse(report["lockfile_membership_proven_by_match"])
        self.assertEqual(report["runtime_sbom"], "not_verified")
        self.assertFalse(report["image_binary"]["dep_v0_section_verified"])

    def test_mismatch(self):
        archive, digest = self.archive([[("garage", elf(), None)]])
        release = self.root / "release"
        release.write_bytes(elf(suffix=b"different"))
        self.assertFalse(compare(archive, digest, "amd64", release)["binary_match"])

    def test_wrong_architecture(self):
        with self.assertRaisesRegex(ValueError, "elf_architecture"):
            fingerprint(io.BytesIO(elf("arm64")), "amd64")

    def test_config_digest(self):
        archive, _ = self.archive([[("garage", elf(), None)]])
        with self.assertRaisesRegex(ValueError, "config_digest"):
            image_fingerprint(archive, "sha256:" + "0" * 64, "amd64")

    def test_layer_digest(self):
        archive, digest = self.archive([[("garage", elf(), None)]], tamper=True)
        with self.assertRaisesRegex(ValueError, "layer_diff_id"):
            image_fingerprint(archive, digest, "amd64")

    def test_link_rejected(self):
        archive, digest = self.archive([[("garage", b"", "/other")]])
        with self.assertRaisesRegex(ValueError, "regular_file"):
            image_fingerprint(archive, digest, "amd64")

    def test_whiteout_and_replacement(self):
        archive, digest = self.archive(
            [[("garage", elf(), None)], [(".wh.garage", b"", None)]]
        )
        with self.assertRaisesRegex(ValueError, "missing"):
            image_fingerprint(archive, digest, "amd64")
        archive, digest = self.archive(
            [
                [("garage", elf(), None)],
                [(".wh..wh..opq", b"", None), ("garage", elf(suffix=b"new"), None)],
            ]
        )
        self.assertEqual(image_fingerprint(archive, digest, "amd64")["size_bytes"], 67)

    def test_path_traversal_rejected(self):
        archive, digest = self.archive([[("../garage", elf(), None)]])
        with self.assertRaisesRegex(ValueError, "unsafe_layer_path"):
            image_fingerprint(archive, digest, "amd64")

    def test_fixed_release_url(self):
        self.assertEqual(
            release_url("arm64"),
            "https://garagehq.deuxfleurs.fr/_releases/v2.5.0/aarch64-unknown-linux-musl/garage",
        )


if __name__ == "__main__":
    unittest.main()
