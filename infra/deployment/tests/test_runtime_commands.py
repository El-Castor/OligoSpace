"""Selected and historical storage runtimes remain explicit, never auto-detected."""

import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


class RuntimeCommandTests(unittest.TestCase):
    def test_storage_runtime_is_explicit_and_rejects_unknown_modes(self):
        spec = importlib.util.spec_from_file_location(
            "qualify_storage", ROOT / "qualify_storage.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(
            module.runtime_command("micromamba"),
            ["micromamba", "run", "--name", "base", "python"],
        )
        self.assertEqual(module.runtime_command("python"), ["/opt/venv/bin/python"])
        with self.assertRaises(ValueError):
            module.runtime_command("sh -c python")
