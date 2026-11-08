"""The scientific dossier must fail if any tested download lacks a faithful audit."""

import copy
import unittest

import run


class ScientificCsvAuditTests(unittest.TestCase):
    def evidence(self):
        return {
            "exports": 6,
            "invalid_audits": 0,
            "distinct_requests": 6,
            "events": copy.deepcopy(run.EXPECTED_CSV_AUDITS),
        }

    def test_exact_ordered_actor_counts_pass(self):
        self.assertTrue(run.csv_audit_passed(self.evidence()))

    def test_wrong_count_or_actor_for_each_download_fails(self):
        for index in range(6):
            with self.subTest(download=index):
                evidence = self.evidence()
                evidence["events"][index]["rows"] += 1
                self.assertFalse(run.csv_audit_passed(evidence))
                evidence = self.evidence()
                evidence["events"][index]["actor"] = "other"
                self.assertFalse(run.csv_audit_passed(evidence))

    def test_missing_audit_or_reused_correlation_fails(self):
        for field in ("exports", "distinct_requests"):
            evidence = self.evidence()
            evidence[field] -= 1
            self.assertFalse(run.csv_audit_passed(evidence))
        evidence = self.evidence()
        evidence["events"].pop(1)
        self.assertFalse(run.csv_audit_passed(evidence))

    def test_invalid_schema_or_unexpected_content_fails(self):
        evidence = self.evidence()
        evidence["invalid_audits"] = 1
        self.assertFalse(run.csv_audit_passed(evidence))
        for value in (None, {}, {"events": "not-an-aggregate"}):
            self.assertFalse(run.csv_audit_passed(value))
        evidence = self.evidence()
        evidence["events"][0]["token"] = "synthetic-unexpected-field"
        self.assertFalse(run.valid_csv_audit_shape(evidence))
