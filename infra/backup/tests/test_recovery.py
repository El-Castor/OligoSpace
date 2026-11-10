from pathlib import Path
import sys
import unittest
from unittest.mock import patch

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

    def test_custom_function_makes_database_nonempty(self):
        obj = object.__new__(Recovery)
        obj.config = {"databases": {"application": {}, "identity": {}}}
        obj._sql = lambda role, sql: "1"
        with self.assertRaisesRegex(ValueError, "nonempty_database_target"):
            obj._empty_databases()

    def test_missing_attachment_reference_refused(self):
        obj = object.__new__(Recovery)
        obj.config = {"buckets": ["bucket"]}
        obj._sql = (
            lambda role, sql: "t"
            if "to_regclass" in sql
            else '[{"object_key":"missing","sha256":"aaa","size_bytes":3,"content_type":"text/plain"}]'
        )
        with self.assertRaisesRegex(ValueError, "attachment_object_integrity_failed"):
            obj._attachment_integrity([{"bucket": "bucket", "objects": []}])

    def test_dump_restore_preserves_owner_and_grants(self):
        import tempfile

        obj = object.__new__(Recovery)
        obj.config = {
            "database_service": "postgres",
            "databases": {"application": {"name": "test", "user": "operator"}},
        }
        obj.dc = ["docker", "compose"]
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "dump"
            p.write_bytes(b"native dump")
            with patch("recovery.subprocess.run") as run:
                run.return_value.returncode = 0
                obj._restore_database("application", p)
                args = run.call_args.args[0]
                self.assertNotIn("--no-owner", args)
                self.assertNotIn("--no-acl", args)
