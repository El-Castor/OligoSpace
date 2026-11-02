import importlib.util
from pathlib import Path
import unittest


class BuilderTests(unittest.TestCase):
    def test_loaded_image_must_match_oci_configuration_and_layers(self):
        path = Path(__file__).resolve().parents[1] / "build_local.py"
        spec = importlib.util.spec_from_file_location("build_local", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "loaded_image_matches"))
        proof = {
            "config_digest": "sha256:" + "a" * 64,
            "rootfs_diff_ids": ["sha256:" + "b" * 64],
        }
        self.assertTrue(
            module.loaded_image_matches(
                {
                    "Id": proof["config_digest"],
                    "RootFS": {"Layers": proof["rootfs_diff_ids"]},
                },
                proof,
            )
        )
        self.assertFalse(
            module.loaded_image_matches(
                {"Id": "other", "RootFS": {"Layers": []}}, proof
            )
        )

    def test_builder_inspect_text_compatibility(self):
        path = Path(__file__).resolve().parents[1] / "build_local.py"
        spec = importlib.util.spec_from_file_location("build_local", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "parse_builder"))
        self.assertEqual(
            module.parse_builder(
                "Name: local\nDriver: docker\nNodes:\nEndpoint: local\n"
            ),
            {"Driver": "docker", "Nodes": [{"Endpoint": "local"}]},
        )

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

    def test_explicit_local_container_builder_can_export_oci_in_ci(self):
        path = Path(__file__).resolve().parents[1] / "build_local.py"
        spec = importlib.util.spec_from_file_location("build_local", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(
            module.validate_builder(
                {"Driver": "docker-container", "Nodes": [{"Endpoint": "default"}]},
                "default",
                {},
            )
        )
        local = {"Driver": "docker", "Nodes": [{"Endpoint": "desktop-linux"}]}
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
