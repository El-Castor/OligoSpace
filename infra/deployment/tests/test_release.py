import importlib.util
from pathlib import Path
import unittest


class ReleaseTests(unittest.TestCase):
    def test_release_requires_native_results_and_qualified_storage(self):
        path = Path(__file__).resolve().parents[1] / "release.py"
        self.assertTrue(path.exists(), "release contract must exist")
        spec = importlib.util.spec_from_file_location("release", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertIn("storage", module.blockers({}))
        self.assertIn(
            "native_architectures", module.blockers({"storage": {"status": "passed"}})
        )
        self.assertIn("source", module.blockers({"source": "development-unpinned"}))


if __name__ == "__main__":
    unittest.main()
