import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import json
import subprocess


class SystemPackagesTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).resolve().parents[1] / "inspect_system_packages.py"
        self.assertTrue(path.exists(), "package inspection helper required")
        spec = importlib.util.spec_from_file_location("system_packages", path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def test_source_versions_are_metadata_not_guessed_from_binary_versions(self):
        row = "login\t1:4.16.0-2+really2.41.5-0+deb13u1\tutil-linux\t2.41.5-0+deb13u1\tinstall ok installed\n"
        result = self.module.parse_metadata(row, "login")
        self.assertEqual(result["source_version"], "2.41.5-0+deb13u1")
        row = "libacl1:amd64\t2.3.2-2+b1\tacl\t2.3.2-2\tinstall ok installed\n"
        self.assertEqual(
            self.module.parse_metadata(row, "libacl1")["source_version"], "2.3.2-2"
        )

    def test_missing_package_and_absent_files_do_not_establish_safety(self):
        self.assertEqual(
            self.module.parse_metadata("", "login")["observation"],
            "package_metadata_unavailable",
        )
        with tempfile.TemporaryDirectory() as directory:
            result = self.module.file_presence([directory + "/missing"])
        self.assertEqual(result["existing_regular_files"], 0)
        self.assertEqual(result["missing_paths"], 1)
        self.assertNotIn("safe", result)

    def test_image_proof_requires_identity_platform_source_and_layers(self):
        proof = {
            "status": "verified",
            "source": "a" * 40,
            "architecture": "amd64",
            "config_digest": "sha256:" + "b" * 64,
            "rootfs_diff_ids": ["sha256:" + "c" * 64],
        }
        loaded = {
            "Id": proof["config_digest"],
            "Architecture": "amd64",
            "Os": "linux",
            "RootFS": {"Layers": proof["rootfs_diff_ids"]},
            "Config": {
                "User": "1000",
                "Labels": {"org.opencontainers.image.revision": proof["source"]},
            },
        }
        self.assertTrue(self.module.image_matches(loaded, proof))
        loaded["RootFS"]["Layers"] = []
        self.assertFalse(self.module.image_matches(loaded, proof))

    def test_read_only_probe_uses_python_without_activation_writes(self):
        proof = {
            "status": "verified",
            "source": "a" * 40,
            "architecture": "amd64",
            "config_digest": "sha256:" + "b" * 64,
            "rootfs_diff_ids": ["sha256:" + "c" * 64],
        }
        loaded = {
            "Id": proof["config_digest"],
            "Architecture": "amd64",
            "Os": "linux",
            "RootFS": {"Layers": proof["rootfs_diff_ids"]},
            "Config": {
                "User": "1000",
                "Labels": {"org.opencontainers.image.revision": proof["source"]},
            },
        }
        calls = []

        def run(argv, **kwargs):
            calls.append(argv)
            if "context" in argv[3:]:
                value = [{"Endpoints": {"docker": {"Host": "unix:///test.sock"}}}]
            elif "image" in argv:
                value = [loaded]
            elif "info" in argv:
                return subprocess.CompletedProcess(argv, 0, "x86_64", "")
            else:
                value = {"execution": "observed"}
            return subprocess.CompletedProcess(argv, 0, json.dumps(value), "")

        with (
            patch.object(self.module.subprocess, "run", side_effect=run),
            patch.dict(
                self.module.os.environ, {"DOCKER_HOST": "", "DOCKER_CONTEXT": ""}
            ),
        ):
            self.module.host("default", proof)
        argv = calls[-1]
        self.assertIn("--read-only", argv)
        self.assertEqual(argv[argv.index("--network") + 1], "none")
        self.assertEqual(argv[argv.index("--entrypoint") + 1], "/opt/conda/bin/python")
        self.assertEqual(argv[argv.index("--entrypoint") + 2], proof["config_digest"])

    def test_failed_command_diagnostics_never_retain_payload(self):
        result = self.module.diagnostic_categories(
            "synthetic-private-value read-only file system lock failed to create"
        )
        self.assertEqual(result, ["read-only file system", "failed to create", "lock"])
        self.assertNotIn("synthetic-private-value", str(result))

    def test_normalized_conda_loader_paths_are_not_silently_lost(self):
        rows = self.module.parse_ldd(
            "libpython3.12.so.1.0 => /opt/conda/bin/../lib/libpython3.12.so.1.0 (0x123)\n"
        )
        self.assertEqual(rows[0]["path"], "/opt/conda/lib/libpython3.12.so.1.0")
        self.assertEqual(rows[0]["origin"], "conda")

    def test_library_classification_retains_only_public_paths(self):
        rows = self.module.parse_ldd(
            "libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x123)\nnoise secret\nlibz.so.1 => /opt/conda/lib/libz.so.1 (0x234)\n"
        )
        self.assertEqual([row["origin"] for row in rows], ["debian_system", "conda"])
        self.assertNotIn("secret", str(rows))
