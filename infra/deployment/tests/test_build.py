import importlib.util
from pathlib import Path
import unittest


class BuilderTests(unittest.TestCase):
    def test_remote_builder_or_environment_override_is_refused(self):
        path = Path(__file__).resolve().parents[1] / "build_local.py"
        spec = importlib.util.spec_from_file_location("build_local", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "validate_builder"))
        local = {"Driver": "docker", "Nodes": [{"Endpoint": "desktop-linux"}]}
        self.assertTrue(module.validate_builder(local, "desktop-linux", {}))
        self.assertFalse(
            module.validate_builder(
                {"Driver": "remote", "Nodes": [{"Endpoint": "tcp://remote"}]},
                "desktop-linux",
                {},
            )
        )
        self.assertFalse(
            module.validate_builder(
                local, "desktop-linux", {"BUILDX_BUILDER": "remote"}
            )
        )
        self.assertFalse(
            module.validate_builder(
                {"Driver": "docker", "Nodes": [{"Endpoint": "other"}]},
                "desktop-linux",
                {},
            )
        )
