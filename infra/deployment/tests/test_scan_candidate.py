import io
import hashlib
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import scan_candidate as candidate


class CandidateTests(unittest.TestCase):
    def test_no_os_metadata_never_fabricates_coverage_or_hides_findings(self):
        proof = {"config_digest": "sha256:" + "a" * 64, "architecture": "arm64"}
        raw = {
            "SchemaVersion": 2,
            "ArtifactType": "container_image",
            "Metadata": {
                "ImageID": proof["config_digest"],
                "ImageConfig": {"architecture": "arm64", "os": "linux"},
            },
            "Results": [{"Secrets": [{"Match": "private"}]}],
        }
        database = {
            "Version": 2,
            **{
                key: "2026-11-02T00:00:00Z"
                for key in ("UpdatedAt", "NextUpdate", "DownloadedAt")
            },
        }
        report = candidate.summarize_candidate(raw, proof, database)
        self.assertEqual(report["gate"], "failed")
        self.assertEqual(report["coverage"]["operating_system"], "not_detected")
        self.assertEqual(report["coverage"]["package_inventory"], "not_verified")
        self.assertNotIn("private", json.dumps(report))
        raw["Results"][0]["Secrets"] = []
        self.assertEqual(
            candidate.summarize_candidate(raw, proof, database)["gate"], "not_verified"
        )
        raw["Metadata"]["ImageID"] = "sha256:" + "0" * 64
        with self.assertRaises(ValueError):
            candidate.summarize_candidate(raw, proof, database)

    def test_registry_payload_requires_exact_digest(self):
        data = b'{"schemaVersion":2}'
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        self.assertEqual(
            candidate.verified_json(data + b"\n", digest), {"schemaVersion": 2}
        )
        with self.assertRaises(ValueError):
            candidate.verified_json(data, "sha256:" + "0" * 64)

    def test_platform_requires_unique_exact_linux_child(self):
        descriptor = {
            "digest": "sha256:" + "a" * 64,
            "platform": {"os": "linux", "architecture": "arm64"},
        }
        self.assertEqual(
            candidate.platform_descriptor({"manifests": [descriptor]}, "arm64"),
            descriptor,
        )
        for descriptors in (
            [],
            [descriptor, descriptor],
            [{**descriptor, "digest": "mutable:tag"}],
        ):
            with self.assertRaises(ValueError):
                candidate.platform_descriptor({"manifests": descriptors}, "arm64")

    def test_archive_config_hash_and_platform_must_match_manifest(self):
        data = json.dumps({"os": "linux", "architecture": "arm64"}).encode()
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            archive = Path(directory) / "image.tar"
            with tarfile.open(archive, "w") as tar:
                for name, content in (
                    ("manifest.json", json.dumps([{"Config": "config.json"}]).encode()),
                    ("config.json", data),
                ):
                    member = tarfile.TarInfo(name)
                    member.size = len(content)
                    tar.addfile(member, io.BytesIO(content))
            candidate.verify_archive(archive, digest, "arm64")
            for wrong_digest, architecture in (
                ("sha256:" + "0" * 64, "arm64"),
                (digest, "amd64"),
            ):
                with self.assertRaises(ValueError):
                    candidate.verify_archive(archive, wrong_digest, architecture)

    def test_inventory_discards_paths_urls_and_secret_text(self):
        raw = {
            "Results": [
                {
                    "Target": "private-path",
                    "Packages": [
                        {
                            "Name": "openssl",
                            "Version": "1.0",
                            "Licenses": ["Apache-2.0"],
                            "FilePath": "private-path",
                        }
                    ],
                    "Licenses": [
                        {"Name": "GPL-3.0", "Severity": "HIGH", "Text": "private-match"}
                    ],
                    "Secrets": [{"Match": "private-match"}],
                }
            ]
        }
        result = candidate.inventory(raw)
        self.assertNotIn("private", json.dumps(result))
        self.assertEqual(result["license_findings"], 1)
        self.assertEqual(result["packages"][0]["name"], "openssl")

    def test_malformed_inventory_fails_closed(self):
        for raw in (
            {"Results": [{"Packages": [{"Name": "bad\nfield", "Version": "1"}]}]},
        ):
            with self.assertRaises(ValueError):
                candidate.inventory(raw)
