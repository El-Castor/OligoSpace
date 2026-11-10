from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from recovery import Recovery


class CoordinationTests(unittest.TestCase):
    def test_backup_always_resumes_original_running_services_on_failure(self):
        obj = object.__new__(Recovery)
        obj.config = {"source_revision": "a" * 40}
        obj._lock = lambda: __import__("contextlib").nullcontext()
        obj._preflight = lambda: None
        obj._running = lambda: ["api", "keycloak"]
        obj._stop = lambda names: None
        obj._assert_stopped = lambda: None
        obj._assert_no_sessions = lambda: (_ for _ in ()).throw(ValueError("active"))
        resumed = []
        obj._resume = lambda names: resumed.extend(names)
        with self.assertRaises(ValueError):
            obj.backup(Path("unused"), Path("unused"))
        self.assertEqual(resumed, ["api", "keycloak"])

    def test_restore_preflight_does_not_start_target(self):
        obj = object.__new__(Recovery)
        obj._lock = lambda: __import__("contextlib").nullcontext()
        obj._preflight = lambda: (_ for _ in ()).throw(ValueError("secrets_missing"))
        with self.assertRaises(ValueError):
            obj.restore(Path("missing"), Path("missing"))
