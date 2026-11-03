"""Evidence validation and outage-signal handshake use synthetic temporary data."""

import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import run


def load_sample() -> dict:
    return {
        "requests_per_phase": 80,
        "results": [
            {
                "endpoint": endpoint,
                "concurrency": level,
                "requests": 80,
                "errors": 0,
                "p50_ms": 12.3,
                "p95_ms": 30.1,
                "max_ms": 55.0,
                "throughput_rps": 210.4,
            }
            for endpoint in run.LOAD_ENDPOINTS
            for level in run.LOAD_LEVELS
        ],
    }


def outage_sample() -> dict:
    return {
        "token_valid_during_outage": True,
        "outage_requests": 26,
        "outage_non_401": 0,
        "outage_p50_ms": 40.0,
        "outage_max_ms": 120.5,
        "health_live_status": 200,
        "ui_session_required": True,
        "recovery_old_token_status": 401,
        "recovery_new_login_status": 200,
        "seconds_to_recover": 18.2,
    }


class EvidenceValidationTests(unittest.TestCase):
    def test_complete_numeric_load_evidence_is_accepted(self):
        self.assertTrue(run.valid_load_evidence(load_sample()))

    def test_free_text_or_extra_fields_are_rejected(self):
        for mutate in (
            lambda value: value["results"][0].update(note="Bearer abc"),
            lambda value: value["results"][0].update(endpoint="/me?token=abc"),
            lambda value: value["results"][0].update(p50_ms="12"),
            lambda value: value.update(extra=1),
            lambda value: value["results"].pop(),
            lambda value: value["results"][1].update(
                endpoint=value["results"][0]["endpoint"],
                concurrency=value["results"][0]["concurrency"],
            ),
        ):
            with self.subTest(mutate=mutate):
                value = copy.deepcopy(load_sample())
                mutate(value)
                self.assertFalse(run.valid_load_evidence(value))

    def test_outage_evidence_is_strictly_typed(self):
        self.assertTrue(run.valid_outage_evidence(outage_sample()))
        for key, bad in (
            ("token_valid_during_outage", "true"),
            ("health_live_status", 99),
            ("outage_non_401", -1),
            ("seconds_to_recover", "18"),
            ("session_cookie", "value"),
        ):
            with self.subTest(key=key):
                value = outage_sample()
                value[key] = bad
                self.assertFalse(run.valid_outage_evidence(value))

    def test_outage_handshake_stops_then_starts_only_when_requested(self):
        script = (
            "import pathlib,sys,time\n"
            "d=pathlib.Path(sys.argv[1])\n"
            "def wait(n):\n"
            "    for _ in range(100):\n"
            "        if (d/n).exists(): return\n"
            "        time.sleep(0.1)\n"
            "    sys.exit(3)\n"
            "(d/'outage-request').write_text('')\n"
            "wait('outage-ack')\n"
            "(d/'restore-request').write_text('')\n"
            "wait('restore-ack')\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            signals = Path(temporary)
            process = subprocess.Popen(
                [sys.executable, "-c", script, str(signals)], text=True
            )
            run.serve_outage_signals(["true"], signals, process)
            self.assertEqual(process.wait(), 0)
            self.assertEqual((signals / "outage-ack").read_text(), "ok")
            self.assertEqual((signals / "restore-ack").read_text(), "ok")

    def test_failed_service_command_is_acknowledged_as_failed(self):
        script = (
            "import pathlib,sys,time\n"
            "d=pathlib.Path(sys.argv[1])\n"
            "(d/'outage-request').write_text('')\n"
            "time.sleep(2)\n"
        )
        with tempfile.TemporaryDirectory() as temporary:
            signals = Path(temporary)
            process = subprocess.Popen(
                [sys.executable, "-c", script, str(signals)], text=True
            )
            run.serve_outage_signals(["false"], signals, process)
            process.wait()
            self.assertEqual((signals / "outage-ack").read_text(), "failed")


if __name__ == "__main__":
    unittest.main()
