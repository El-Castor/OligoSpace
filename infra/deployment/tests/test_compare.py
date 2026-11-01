import importlib.util
from pathlib import Path
import unittest


class ComparisonTests(unittest.TestCase):
    def test_numeric_tolerance_never_hides_units_or_parameter_drift(self):
        path = Path(__file__).resolve().parents[1] / "collect_reports.py"
        self.assertTrue(path.exists())
        spec = importlib.util.spec_from_file_location("collect_reports", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        a = {"value": 59.626630, "unit": "degC"}
        report = module.compare_payloads(a, {**a, "value": 59.6266305})
        self.assertLess(report["max_absolute_delta"], 1e-6)
        with self.assertRaises(ValueError):
            module.compare_payloads(a, {**a, "unit": "K"})
        with self.assertRaises(ValueError):
            module.compare_payloads(a, {**a, "value": float("nan")})
        with self.assertRaises(ValueError):
            module.compare_payloads(a, {**a, "value": 59.7})
