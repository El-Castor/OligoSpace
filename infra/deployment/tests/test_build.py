import importlib.util
import copy
from pathlib import Path
import unittest
import io
import json
import sys
import tarfile
import tempfile
from types import SimpleNamespace
from unittest.mock import patch


class BuilderTests(unittest.TestCase):
    def load_module(self):
        path = Path(__file__).resolve().parents[1] / "build_local.py"
        spec = importlib.util.spec_from_file_location("build_local", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_experiment_dispatch_has_fixed_recipe_target_and_distinct_tag(self):
        module = self.load_module()
        sha = "a" * 40
        for role in ("api", "worker"):
            for experiment in (
                "strategy-a",
                "strategy-b",
                "strategy-c",
                "strategy-c-ubuntu",
            ):
                recipe = module.build_recipe(role, sha, experiment)
                self.assertEqual(
                    recipe["dockerfile"],
                    f"infra/hardening/strategies/Dockerfile.{role}",
                )
                self.assertEqual(
                    recipe["tag"], f"oligospace-qualification/{role}-{experiment}:{sha}"
                )
                self.assertIn(experiment, recipe["arguments"])
                self.assertIn(
                    "MINIMAL_BASE=debian:trixie-slim@sha256:a72b4433de1cf7d6bae0c4cee74d0547f58601a643b3375f070c51600d63b6b2",
                    recipe["arguments"],
                )
        baseline = module.build_recipe("api", sha, None)
        self.assertEqual(baseline["tag"], f"oligospace-qualification/api:{sha}")
        self.assertEqual(baseline["arguments"], [])
        for role, experiment in (("web", "strategy-a"), ("api", "other")):
            with self.assertRaises(ValueError):
                module.build_recipe(role, sha, experiment)

    def test_source_ref_requires_full_commit_and_archive_uses_it(self):
        module = self.load_module()
        sha = "9ebbf2cd993395af2b154efb0b4cf5a76b4dd079"
        self.assertEqual(module.source_revision(sha, "a" * 40), sha)
        self.assertEqual(module.source_revision(None, "a" * 40), "a" * 40)
        for invalid in ("HEAD", "main", "9ebbf2c", "-" + "a" * 39, "z" * 40):
            with self.assertRaises(ValueError):
                module.source_revision(invalid, "a" * 40)

    def test_baseline_archive_manifest_and_image_label_use_requested_commit(self):
        module = self.load_module()
        source = "9ebbf2cd993395af2b154efb0b4cf5a76b4dd079"
        controller = "a" * 40
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w"):
            pass
        archived = []

        def output(command, **kwargs):
            if command[:3] == ["git", "rev-parse", "HEAD"]:
                return controller + "\n"
            if command[:3] == ["git", "cat-file", "-t"]:
                return "commit\n"
            if command[:2] == ["git", "archive"]:
                archived.append(command[2])
                return stream.getvalue()
            if "context" in command and "inspect" in command:
                return b'[{"Endpoints":{"docker":{"Host":"unix:///synthetic"}}}]'
            if "buildx" in command:
                return "Driver: docker\nEndpoint: test\n"
            if "info" in command:
                return "arm64\n"
            raise AssertionError(command)

        def run(command, **kwargs):
            if command[:2] == ["git", "diff"]:
                self.assertEqual(command, ["git", "diff", "--quiet", "HEAD"])
                return
            self.assertIn(f"oligospace-qualification/api:{source}", command)
            self.assertIn("org.opencontainers.image.revision=" + source, command)
            Path(command[command.index("--metadata-file") + 1]).write_text("{}")

        with tempfile.TemporaryDirectory() as directory:
            argv = [
                "build",
                "--context",
                "test",
                "--architecture",
                "arm64",
                "--role",
                "api",
                "--source-ref",
                source,
                "--output",
                directory,
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(module.subprocess, "check_output", side_effect=output),
                patch.object(module.subprocess, "run", side_effect=run),
                patch.dict(module.os.environ, {}, clear=True),
                patch.dict(
                    sys.modules,
                    {
                        "oci": SimpleNamespace(verify_oci=lambda *args: {}),
                        "retain_supply_chain": SimpleNamespace(
                            retain_supply_chain=lambda *args: {}
                        ),
                    },
                ),
            ):
                module.main()
            manifest = json.loads(
                (Path(directory) / "qualification-manifest.json").read_text()
            )
        self.assertEqual(archived, [source])
        self.assertEqual(manifest["source"], source)
        self.assertEqual(manifest["controller_source"], controller)
        self.assertIsNone(manifest["experiment"])

    def test_platform_manifest_identity_accepts_exact_verified_image_only(self):
        path = Path(__file__).resolve().parents[1] / "build_local.py"
        spec = importlib.util.spec_from_file_location("build_local", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        proof = {
            "config_digest": "sha256:" + "a" * 64,
            "rootfs_diff_ids": ["sha256:" + "b" * 64],
            "architecture": "arm64",
            "descriptor": {
                "digest": "sha256:" + "c" * 64,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
                "platform": {"os": "linux", "architecture": "arm64"},
            },
        }
        loaded = {
            "Id": "sha256:" + "c" * 64,
            "Descriptor": {
                "digest": "sha256:" + "c" * 64,
                "mediaType": "application/vnd.oci.image.manifest.v1+json",
            },
            "Architecture": "arm64",
            "Os": "linux",
            "RootFS": {"Layers": ["sha256:" + "b" * 64]},
        }
        self.assertTrue(module.loaded_image_matches(loaded, proof))
        for key, value in [
            ("Id", proof["config_digest"]),
            ("Id", "sha256:" + "d" * 64),
            ("Architecture", "amd64"),
            ("Os", "windows"),
            ("RootFS", {"Layers": []}),
            ("Descriptor", {"digest": "sha256:" + "d" * 64}),
            (
                "Descriptor",
                {
                    "digest": loaded["Id"],
                    "mediaType": "application/vnd.oci.image.index.v1+json",
                },
            ),
        ]:
            with self.subTest(key=key, value=value):
                invalid = copy.deepcopy(loaded)
                invalid[key] = value
                self.assertFalse(module.loaded_image_matches(invalid, proof))

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
