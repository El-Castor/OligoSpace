from __future__ import annotations

import subprocess
import time
from datetime import UTC, datetime
from typing import Any

import psycopg
import pytest

from oligospace_bioinfo import tasks

JOB: dict[str, Any] = {
    "id": "job-1",
    "public_id": "SJOB-000001",
    "attempt_id": "attempt-1",
    "attempt_number": 1,
    "max_attempts": 3,
}
ANALYSIS: dict[str, Any] = {
    "provenance": {"tool": "primer3", "version": "2.6.1"},
    "result": {"tm_c": 42.5},
    "warnings": [],
}


class FakeCursor:
    def __init__(self, job_row: tuple[Any, ...] | None, attempt_row: tuple[Any, ...] | None):
        self.rows = [job_row, attempt_row]
        self.statements: list[str] = []

    def __enter__(self) -> FakeCursor:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def execute(self, statement: str, parameters: tuple[Any, ...] = ()) -> None:
        self.statements.append(" ".join(statement.split()))

    def fetchone(self) -> tuple[Any, ...] | None:
        return self.rows.pop(0)


class FakeConnection:
    def __init__(self, cursor: FakeCursor):
        self._cursor = cursor

    def __enter__(self) -> FakeConnection:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def cursor(self) -> FakeCursor:
        return self._cursor


def _install(
    monkeypatch: pytest.MonkeyPatch,
    job_row: tuple[Any, ...] | None,
    attempt_row: tuple[Any, ...] | None,
) -> FakeCursor:
    cursor = FakeCursor(job_row, attempt_row)
    monkeypatch.setattr(psycopg, "connect", lambda *args, **kwargs: FakeConnection(cursor))
    return cursor


def _writes(cursor: FakeCursor) -> list[str]:
    return [statement for statement in cursor.statements if not statement.startswith("SELECT")]


def test_current_attempt_commits_result(monkeypatch: pytest.MonkeyPatch) -> None:
    cursor = _install(monkeypatch, ("running", 1), ("running",))
    assert tasks._lock_current_attempt(cursor, JOB, datetime.now(UTC)) is True
    assert all("FOR UPDATE" in statement for statement in cursor.statements)
    assert _writes(cursor) == []


def test_superseded_attempt_cannot_succeed(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reconciliation already failed attempt 1 and claimed attempt 2.
    cursor = _install(monkeypatch, ("running", 2), ("failed",))
    assert tasks._succeed(JOB, ANALYSIS) is False
    writes = _writes(cursor)
    assert len(writes) == 1
    assert "'stale_attempt_rejected'" in writes[0]
    assert not any("scientific_job_results" in statement for statement in writes)


def test_stale_running_attempt_is_closed_without_touching_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = _install(monkeypatch, ("succeeded", 2), ("running",))
    assert tasks._succeed(JOB, ANALYSIS) is False
    writes = _writes(cursor)
    assert "error_code='stale_attempt'" in writes[0]
    assert "'stale_attempt_rejected'" in writes[1]
    assert not any(statement.startswith("UPDATE scientific_jobs") for statement in writes)


def test_superseded_attempt_failure_does_not_schedule_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cursor = _install(monkeypatch, ("running", 2), ("failed",))
    error = tasks.ScientificToolError("tool_timeout", "Primer3 timed out.", retryable=True)
    assert tasks._fail(JOB, error) == "stale"
    assert not any(statement.startswith("UPDATE scientific_jobs") for statement in _writes(cursor))


def test_current_attempt_failure_reports_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    cursor = _install(monkeypatch, ("running", 1), ("running",))
    error = tasks.ScientificToolError("tool_timeout", "Primer3 timed out.", retryable=True)
    assert tasks._fail(JOB, error) == "retrying"
    assert any("'scientific_job'" in statement for statement in _writes(cursor))


def test_tool_timeout_is_bounded_by_attempt_lease(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SCIENTIFIC_TOOL_TIMEOUT_SECONDS", "30")
    token = tasks._attempt_deadline.set(time.monotonic() + 10)
    try:
        assert 0 < tasks._tool_timeout() <= 10
    finally:
        tasks._attempt_deadline.reset(token)
    assert tasks._tool_timeout() == 30


def test_exhausted_lease_stops_before_running_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: object, **kwargs: object) -> None:
        raise AssertionError("Primer3 must not start after the lease is exhausted.")

    monkeypatch.setattr(subprocess, "run", forbidden)
    token = tasks._attempt_deadline.set(time.monotonic() - 1)
    try:
        with pytest.raises(tasks.ScientificToolError) as raised:
            tasks._run_tool(["oligotm", "ACGT"])
    finally:
        tasks._attempt_deadline.reset(token)
    assert raised.value.code == "lease_exhausted"
    assert raised.value.retryable is True
