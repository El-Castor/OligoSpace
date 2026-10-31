from __future__ import annotations

import os

import pytest
from sqlalchemy.engine import make_url
from test_laboratory_routes import laboratory_client as laboratory_client
from test_workspace_routes import workspace_client as workspace_client

TEST_DATABASE_ENV = "OLIGOSPACE_TEST_DATABASE_URL"
REQUIRE_INTEGRATION_ENV = "OLIGOSPACE_REQUIRE_INTEGRATION"


@pytest.fixture
def integration_database_url() -> str:
    """Return the integration database URL, refusing anything that is not a `_test` database.

    Integration tests create and mutate rows; they must never run against development or
    production data.
    """
    url = os.environ[TEST_DATABASE_ENV]
    database = make_url(url).database or ""
    if not database.endswith("_test"):
        pytest.fail(
            f"{TEST_DATABASE_ENV} must target a database whose name ends with '_test' "
            f"(got {database!r})"
        )
    return url


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Fail dedicated integration runs that skipped tests instead of reporting them as green."""
    if os.environ.get(REQUIRE_INTEGRATION_ENV) != "1":
        return
    reporter = session.config.pluginmanager.get_plugin("terminalreporter")
    skipped = len(reporter.stats.get("skipped", [])) if reporter is not None else 0
    if skipped:
        if reporter is not None:
            reporter.write_line(
                f"{REQUIRE_INTEGRATION_ENV}=1: {skipped} integration test(s) skipped", red=True
            )
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
