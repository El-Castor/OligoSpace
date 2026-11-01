import importlib.util
from pathlib import Path
import unittest


class GHCRTests(unittest.TestCase):
    def test_plan_is_proposal_only_never_authorization(self):
        path = Path(__file__).resolve().parents[1] / "ghcr_plan.py"
        spec = importlib.util.spec_from_file_location("ghcr_plan", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        report = module.publication_plan("El-Castor/OligoSpace", "a" * 40)
        self.assertFalse(report["publishing_authorized"])
        self.assertFalse(report["packages_created"])
        self.assertNotIn("latest", str(report))
        with self.assertRaises(ValueError):
            module.publication_plan("El-Castor/OligoSpace", "main")
