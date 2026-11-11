import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from maintenance import disposable_project, revision_status


class MaintenanceTests(unittest.TestCase):
    def test_real_project_is_never_an_execution_target(self):
        self.assertFalse(disposable_project("oligospace-pilot"))
        self.assertFalse(disposable_project("oligospace"))
        self.assertTrue(disposable_project("oligospace-pilot-test-123abc"))

    def test_schema_check_never_upgrades_or_downgrades(self):
        self.assertEqual(revision_status(["0004_scientific_jobs"]), "PASS")
        for value in [
            [],
            ["unknown"],
            ["0003_experiment_evidence"],
            ["0004_scientific_jobs", "unknown"],
        ]:
            self.assertEqual(revision_status(value), "BLOCKED")
