import importlib.util
from pathlib import Path
import unittest


class ComparisonTests(unittest.TestCase):
    def test_validated_reference_requires_identical_inputs_and_tool(self):
        path = Path(__file__).resolve().parents[1] / "collect_reports.py"
        spec = importlib.util.spec_from_file_location("collect_reports", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        reference = {
            "inputs": {"dna": "ACGT"},
            "parameters": {"salt": 50},
            "tool_version": "2.6.1",
            "payload": {"tm": 50.0},
        }
        current = {**reference, "source": "new"}
        self.assertEqual(
            module.compare_reference(current, reference)["max_absolute_delta"], 0
        )
        with self.assertRaises(ValueError):
            module.compare_reference(
                {**current, "tool_version": "different"}, reference
            )
        with self.assertRaises(ValueError):
            module.compare_reference({**current, "payload": {"tm": 51.0}}, reference)

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
