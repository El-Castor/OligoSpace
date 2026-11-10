import importlib.util
from pathlib import Path
import unittest
import subprocess


spec = importlib.util.spec_from_file_location(
    "isolated_runtime", Path(__file__).parents[1] / "isolated_runtime.py"
)
module = importlib.util.module_from_spec(spec)


class IsolationTests(unittest.TestCase):
    def setUp(self):
        spec.loader.exec_module(module)

    def test_failed_log_collection_cannot_prove_credentials_absent(self):
        for status, output, expected in (
            (0, "safe", True),
            (1, "", False),
            (0, "private", False),
        ):
            result = subprocess.CompletedProcess([], status, output, "")
            self.assertEqual(module.log_evidence_passed(result, ("private",)), expected)

    def test_all_services_are_bounded_internal_and_have_no_host_ports(self):
        config = module.compose_spec(
            "api-image",
            "worker-image",
            "pg-image",
            "redis-image",
            Path("/tmp/credentials"),
        )
        self.assertTrue(config["networks"]["isolated"]["internal"])
        for name, service in config["services"].items():
            with self.subTest(service=name):
                self.assertTrue(service["read_only"])
                self.assertEqual(service["cap_drop"], ["ALL"])
                self.assertEqual(service["security_opt"], ["no-new-privileges:true"])
                self.assertNotIn("ports", service)
                self.assertNotEqual(service["user"].split(":")[0], "0")
                self.assertGreater(service["pids_limit"], 0)
                self.assertIn("size=", service["tmpfs"][0])
                self.assertNotIn("docker.sock", str(service))

    def test_inspection_rejects_unsafe_runtime_instead_of_trusting_compose(self):
        safe = {
            "Config": {"User": "1000:1000"},
            "HostConfig": {
                "ReadonlyRootfs": True,
                "CapDrop": ["ALL"],
                "SecurityOpt": ["no-new-privileges:true"],
                "Privileged": False,
                "PidsLimit": 128,
                "Memory": 268435456,
                "NanoCpus": 1000000000,
                "PortBindings": {},
                "Tmpfs": {"/tmp": "size=64m"},
            },
            "Mounts": [],
            "NetworkSettings": {"Networks": {"unique_isolated": {}}},
            "State": {"Running": True},
        }
        self.assertTrue(module.runtime_safe(safe, "unique_isolated"))
        for field, value in (
            ("Privileged", True),
            ("ReadonlyRootfs", False),
            ("PortBindings", {"8000/tcp": []}),
            ("PidsLimit", 0),
        ):
            altered = {**safe, "HostConfig": {**safe["HostConfig"], field: value}}
            self.assertFalse(module.runtime_safe(altered, "unique_isolated"))
        self.assertFalse(
            module.runtime_safe(
                {**safe, "Mounts": [{"Source": "/var/run/docker.sock", "RW": False}]},
                "unique_isolated",
            )
        )


if __name__ == "__main__":
    unittest.main()
