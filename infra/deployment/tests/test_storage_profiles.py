import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import sys
import tomllib
import unittest


class StorageProfileTests(unittest.TestCase):
    def profile_module(self):
        path = Path(__file__).resolve().parents[1] / "storage_profiles.py"
        spec = importlib.util.spec_from_file_location("storage_profiles", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_garage_keeps_metadata_and_objects_in_persistent_mount(self):
        module = self.profile_module()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            profile = module.prepare(
                "garage", "synthetic-source", root, "GK" + "a" * 32, "b" * 64
            )
            config = tomllib.loads((root / "garage.toml").read_text())
            self.assertEqual(config["metadata_dir"], "/data/meta")
            self.assertEqual(config["data_dir"], "/data/objects")
            self.assertEqual(config["s3_api"]["s3_region"], "us-east-1")
            self.assertEqual(config["replication_factor"], 1)
            self.assertTrue(config["metadata_fsync"])
            self.assertTrue(config["data_fsync"])
            self.assertIn("--default-access-key", profile["command"])
            self.assertNotIn("--default-bucket", profile["command"])
            self.assertEqual(profile["environment"]["RUST_LOG"], "warn")
            self.assertEqual((root / "garage.toml").stat().st_mode & 0o777, 0o600)

    def test_both_candidates_resolve_as_private_digest_pinned_compose(self):
        module = self.profile_module()
        for kind in ("seaweedfs", "garage"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                module.prepare(
                    kind, "synthetic-source", root, "GK" + "a" * 32, "b" * 64
                )
                env = root / "credentials.env"
                env.write_text("SYNTHETIC_ONLY=1\n")
                definition = module.compose_definition(
                    kind, "source", "oligospace-deploy02-test-unit", root, env
                )
                path = root / "compose.json"
                path.write_text(json.dumps(definition))
                resolved = json.loads(
                    subprocess.check_output(
                        [
                            "docker",
                            "compose",
                            "--project-name",
                            "oligospace-deploy02-test-unit",
                            "--file",
                            str(path),
                            "config",
                            "--format",
                            "json",
                        ]
                    )
                )
                service = resolved["services"]["source"]
                self.assertIn("@sha256:", service["image"])
                self.assertFalse(service.get("ports"))
                self.assertNotEqual(service.get("network_mode"), "host")
                self.assertTrue(resolved["networks"]["default"]["external"])
                self.assertEqual(
                    resolved["networks"]["default"]["name"],
                    "oligospace-deploy02-test-unit",
                )
                self.assertTrue(any(v["target"] == "/data" for v in service["volumes"]))

    def test_aistor_is_not_an_executable_profile(self):
        module = self.profile_module()
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                module.prepare("aistor", "synthetic", Path(directory), "a", "b")

    def test_unavailable_engine_never_reports_compatibility_success(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "docker"
            executable.write_text(
                f"#!{sys.executable}\n"
                "import json, sys\n"
                "if 'inspect' in sys.argv and 'context' in sys.argv:\n"
                " print(json.dumps([{'Endpoints': {'docker': {'Host': 'unix:///synthetic.sock'}}}]))\n"
                "else:\n"
                " sys.exit(1)\n"
            )
            executable.chmod(0o700)
            report_dir = root / "evidence"
            script = Path(__file__).resolve().parents[1] / "qualify_storage.py"
            env = {k: v for k, v in os.environ.items() if k != "DOCKER_HOST"}
            env["PATH"] = str(root) + os.pathsep + env.get("PATH", "")
            process = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--context",
                    "synthetic",
                    "--source",
                    "garage",
                    "--target",
                    "garage",
                    "--api-image",
                    "synthetic-not-executed",
                    "--output",
                    str(report_dir),
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(process.returncode, 0)
            report = json.loads((report_dir / "storage-report.json").read_text())
            self.assertEqual(report["status"], "blocked")
            self.assertFalse(report["application_adapter_exercised"])
            self.assertEqual(report["checks"], [])
            self.assertEqual(report["stage"], "engine_availability")

    def lifecycle_failure(self, failure):
        # Stub only the unavailable Docker boundary; test the real CLI lifecycle.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "docker"
            executable.write_text(
                f"#!{sys.executable}\n"
                "import json, os, pathlib, sys\n"
                "args = sys.argv[3:]\n"
                "if args[:2] == ['context', 'inspect']:\n"
                " print(json.dumps([{'Endpoints': {'docker': {'Host': 'unix:///synthetic.sock'}}}]))\n"
                "elif args[0] == 'info':\n"
                " print(json.dumps({'Architecture': 'aarch64', 'OSType': 'linux'}))\n"
                "elif args[:2] == ['network', 'inspect']:\n"
                " print(json.dumps([{'Internal': True}]))\n"
                "elif args[0] == 'inspect':\n"
                " print(json.dumps([{'HostConfig': {'PortBindings': {}, 'NetworkMode': 'synthetic'}}]))\n"
                "elif args[0] == 'stats':\n"
                " p = pathlib.Path(os.environ['STAT_COUNTER'])\n"
                " n = int(p.read_text()) + 1 if p.exists() else 1\n"
                " p.write_text(str(n))\n"
                " if n > 2 and os.environ['FAILURE_MODE'] == 'resources': sys.exit(1)\n"
                " print('1MiB / 1GiB')\n"
                "elif args[:2] == ['image', 'inspect']:\n"
                " print(json.dumps({'Architecture': 'arm64'}))\n"
                "elif args[0] == 'rm' and os.environ['FAILURE_MODE'] == 'cleanup':\n"
                " sys.exit(1)\n"
            )
            executable.chmod(0o700)
            report_dir = root / "evidence"
            env = {k: v for k, v in os.environ.items() if k != "DOCKER_HOST"}
            env["PATH"] = str(root) + os.pathsep + env.get("PATH", "")
            env["STAT_COUNTER"] = str(root / "stats")
            env["FAILURE_MODE"] = failure
            script = Path(__file__).resolve().parents[1] / "qualify_storage.py"
            process = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--context",
                    "synthetic",
                    "--source",
                    "garage",
                    "--target",
                    "garage",
                    "--api-image",
                    "synthetic-not-executed",
                    "--output",
                    str(report_dir),
                ],
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(process.returncode, 0)
            report = json.loads((report_dir / "storage-report.json").read_text())
            self.assertEqual(report["status"], "failed")

    def test_late_resource_failure_cannot_leave_a_passed_report(self):
        self.lifecycle_failure("resources")

    def test_cleanup_failure_cannot_leave_a_passed_report(self):
        self.lifecycle_failure("cleanup")


if __name__ == "__main__":
    unittest.main()
