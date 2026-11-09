import importlib.util
import json
from pathlib import Path
import re
import tomllib
import unittest
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
LOCKS = ROOT / "infra/hardening/locks"


class DependencyLockTests(unittest.TestCase):
    def module(self):
        spec = importlib.util.spec_from_file_location(
            "freeze_dependencies", LOCKS.parent / "freeze_dependencies.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_pyproject_pins_and_extras_are_retained_without_root_upgrades(self):
        for role, project in (
            ("api", "apps/api"),
            ("worker", "services/bioinfo-worker"),
        ):
            pins = dict(
                re.findall(
                    r"^([a-z0-9-]+(?:\[[a-z0-9,._-]+\])?)==([^\s]+)",
                    (LOCKS / (role + ".txt")).read_text(),
                    re.M,
                )
            )
            metadata = tomllib.loads((ROOT / project / "pyproject.toml").read_text())
            for requirement in metadata["project"]["dependencies"]:
                name, version = requirement.split("==")
                self.assertEqual(pins[name], version)
            self.assertEqual(pins["kombu"], "5.6.2")
            graph = json.loads(
                (LOCKS / "inputs" / (role + "-dependencies.json")).read_text()
            )
            self.assertEqual(len(pins), len(graph["packages"]))
            for package in graph["packages"]:
                key = package["name"] + (
                    "[" + ",".join(package["extras"]) + "]" if package["extras"] else ""
                )
                self.assertEqual(pins[key], package["version"])

    def test_release_metadata_matches_exact_versions_and_valid_hashes(self):
        module = self.module()
        provenance = json.loads((LOCKS / "provenance.json").read_text())
        for release, metadata in provenance["release_metadata"].items():
            name, version = release.split("==")
            module.validate_release(name, version, metadata)
        with self.assertRaises(ValueError):
            module.validate_release(
                "kombu",
                "5.6.2",
                {
                    "url": "https://evil.example/",
                    "hashes": ["a" * 64],
                    "metadata_sha256": "b" * 64,
                },
            )

    def test_build_root_is_included_explicitly(self):
        module = self.module()
        graph = json.loads((LOCKS / "inputs/build-dependencies.json").read_text())
        packages = module.graph_packages(
            graph, include_root=True, root_version="1.27.0"
        )
        self.assertIn(
            {"name": "hatchling", "version": "1.27.0", "extras": []}, packages
        )
        self.assertNotIn("hatchling", [p["name"] for p in module.graph_packages(graph)])

    def test_generation_from_preserved_receipts_reproduces_lock_bytes_offline(self):
        module = self.module()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            with patch.object(
                module,
                "fetch_release",
                side_effect=AssertionError("network forbidden"),
            ):
                module.generate(
                    {
                        role: LOCKS / "inputs" / (role + "-dependencies.json")
                        for role in ("api", "worker", "build")
                    },
                    output,
                    "1.27.0",
                    LOCKS / "provenance.json",
                )
            for role in ("api", "worker", "build"):
                self.assertEqual(
                    (output / (role + ".txt")).read_bytes(),
                    (LOCKS / (role + ".txt")).read_bytes(),
                )

    def test_export_tracks_extras_markers_and_excludes_optional_dev(self):
        module = self.module()
        requires = {
            "root": ["child[crypto]==1", "dev==1; extra == 'dev'"],
            "child": ["cryptography==1; extra == 'crypto'"],
            "cryptography": [],
        }
        with (
            patch.object(
                module.metadata,
                "distribution",
                side_effect=lambda name: SimpleNamespace(requires=requires[name]),
            ),
            patch.object(module.metadata, "version", return_value="1"),
        ):
            graph = module.export_closure("root")
        self.assertEqual(
            [p["name"] for p in graph["packages"]], ["child", "cryptography"]
        )
        self.assertEqual(graph["packages"][0]["extras"], ["crypto"])


if __name__ == "__main__":
    unittest.main()
