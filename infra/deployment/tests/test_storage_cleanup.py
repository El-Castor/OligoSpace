import importlib.util
from pathlib import Path
import tempfile
import unittest


class CleanupTests(unittest.TestCase):
    def test_failed_resource_cleanup_still_removes_generated_credentials(self):
        path = Path(__file__).resolve().parents[1] / "qualify_storage.py"
        import sys

        sys.path.insert(0, str(path.parent))
        spec = importlib.util.spec_from_file_location("qualify_storage", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "cleanup_disposable"))
        with tempfile.TemporaryDirectory() as directory:
            env = Path(directory) / "synthetic.env"
            env.write_text("synthetic-generated-credentials")
            calls = []

            def failing(*args):
                calls.append(args)
                raise RuntimeError("engine unavailable")

            module.cleanup_disposable(failing, ["one", "two"], "network", [env])
            self.assertFalse(env.exists())
            self.assertEqual(len(calls), 3)
