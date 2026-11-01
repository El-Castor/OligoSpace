import importlib.util
from pathlib import Path
import unittest


class BootstrapTests(unittest.TestCase):
    def test_unknown_schema_is_refused_and_head_is_noop(self):
        path = Path(__file__).resolve().parents[1] / "bootstrap.py"
        self.assertTrue(path.exists(), "controlled bootstrap must exist")
        spec = importlib.util.spec_from_file_location("bootstrap", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertEqual(module.migration_action([]), "upgrade")
        self.assertEqual(module.migration_action(["0004_scientific_jobs"]), "noop")
        with self.assertRaises(ValueError):
            module.migration_action(["unrecognized_schema"])
        with self.assertRaises(ValueError):
            module.migration_action(
                ["0003_experiment_evidence", "0004_scientific_jobs"]
            )

    def test_existing_elevated_or_member_role_is_refused(self):
        path = Path(__file__).resolve().parents[1] / "bootstrap.py"
        spec = importlib.util.spec_from_file_location("bootstrap", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.assertTrue(hasattr(module, "role_is_bounded"))
        bounded = {
            "rolsuper": False,
            "rolcreatedb": False,
            "rolcreaterole": False,
            "rolreplication": False,
            "rolbypassrls": False,
            "member": False,
        }
        self.assertTrue(module.role_is_bounded(bounded))
        for key in bounded:
            self.assertFalse(module.role_is_bounded({**bounded, key: True}))


if __name__ == "__main__":
    unittest.main()
