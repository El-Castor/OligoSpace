import importlib.util
from pathlib import Path
import unittest
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch


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

    def test_migration_uses_active_interpreter_and_holds_connection(self):
        path = Path(__file__).resolve().parents[1] / "bootstrap.py"
        spec = importlib.util.spec_from_file_location("bootstrap", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        connection = SimpleNamespace(
            execute=AsyncMock(),
            fetchval=AsyncMock(side_effect=[None, 0]),
            fetch=AsyncMock(return_value=[{"version_num": module.HEAD}]),
            close=AsyncMock(),
        )

        def migration(command, **kwargs):
            self.assertEqual(
                command, ["/active/python", "-m", "alembic", "upgrade", "head"]
            )
            self.assertFalse(connection.close.called)
            connection.execute.assert_any_await("SELECT pg_advisory_lock(79103002)")
            self.assertFalse(kwargs.get("shell", False))
            return Mock(returncode=0)

        asyncpg = SimpleNamespace(connect=AsyncMock(return_value=connection))
        with (
            patch.dict("sys.modules", {"asyncpg": asyncpg}),
            patch.dict(
                module.os.environ,
                {
                    "DEPLOY_TARGET": "disposable",
                    "PILOT_PROJECT": "oligospace-deploy01-test-unit",
                    "DATABASE_URL": "postgresql+asyncpg://synthetic",
                },
            ),
            patch.object(module.sys, "executable", "/active/python"),
            patch.object(module.subprocess, "run", side_effect=migration),
        ):
            self.assertEqual(asyncio.run(module.migrate()), "upgrade")
        connection.close.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
