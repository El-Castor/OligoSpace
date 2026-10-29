from __future__ import annotations

import os
import re
import subprocess
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime, timedelta
from typing import Any

import psycopg
from celery import Task
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from oligospace_bioinfo import __version__
from oligospace_bioinfo.celery_app import app

PRIMER3_VERSION = "2.6.1"
PRIMER3_SOURCE_SHA256 = "805cef7ef39607cd40f0f5bb8b32e35e20007153a0a55131dd430ce644c8fb9e"
WRAPPER_CONTRACT_VERSION = "primer3-cli-v1"
RESULT_SCHEMA_VERSION = "primer3-results-v1"
_UNAMBIGUOUS_DNA = re.compile(r"^[ACGT]+$")
# Tool calls stop this long before the claimed lease expires, so reconciliation never
# observes an expired lease while the owning attempt can still be executing Primer3.
LEASE_SAFETY_MARGIN_SECONDS = 5.0
_attempt_deadline: ContextVar[float | None] = ContextVar("attempt_deadline", default=None)


class ScientificToolError(RuntimeError):
    def __init__(self, code: str, summary: str, *, retryable: bool = False) -> None:
        super().__init__(summary)
        self.code = code
        self.summary = summary
        self.retryable = retryable


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL", "postgresql://oligospace:change-me@postgres:5432/oligospace"
    ).replace("postgresql+asyncpg://", "postgresql://", 1)


def _lease_seconds() -> int:
    return int(os.environ.get("SCIENTIFIC_JOB_LEASE_SECONDS", "120"))


def _tool_timeout() -> float:
    timeout = float(os.environ.get("SCIENTIFIC_TOOL_TIMEOUT_SECONDS", "30"))
    deadline = _attempt_deadline.get()
    if deadline is None:
        return timeout
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise ScientificToolError(
            "lease_exhausted", "Attempt lease exhausted before Primer3 completed.", retryable=True
        )
    return min(timeout, remaining)


def _run_tool(arguments: list[str]) -> str:
    try:
        completed = subprocess.run(
            arguments,
            check=True,
            capture_output=True,
            text=True,
            timeout=_tool_timeout(),
        )
    except subprocess.TimeoutExpired as exc:
        raise ScientificToolError(
            "tool_timeout", "Primer3 execution timed out.", retryable=True
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise ScientificToolError("tool_exit", "Primer3 rejected the qualified input.") from exc
    return completed.stdout.strip()


def _tool_version() -> str:
    output = _run_tool(["primer3_core", "--about"])
    match = re.search(r"(?:release|version)\s+([0-9]+\.[0-9]+\.[0-9]+)", output, re.I)
    if match is None:
        raise ScientificToolError(
            "invalid_tool_output", "Primer3 version could not be established."
        )
    version = match.group(1)
    if version != PRIMER3_VERSION:
        raise ScientificToolError(
            "tool_version_mismatch",
            f"Expected Primer3 {PRIMER3_VERSION}, observed {version}.",
        )
    return version


def _number(arguments: list[str]) -> float:
    raw = _run_tool(arguments)
    try:
        value = float(raw)
    except ValueError as exc:
        raise ScientificToolError(
            "invalid_tool_output", "Primer3 returned a non-numeric result."
        ) from exc
    if value != value or value in (float("inf"), float("-inf")):
        raise ScientificToolError("invalid_tool_output", "Primer3 returned a non-finite result.")
    return value


def _shared_arguments(parameters: dict[str, Any]) -> list[str]:
    return [
        "-mv",
        str(parameters["mv_conc_mM"]),
        "-dv",
        str(parameters["dv_conc_mM"]),
        "-n",
        str(parameters["dntp_conc_mM"]),
        "-d",
        str(parameters["dna_conc_nM"]),
    ]


def _component(
    value: float, *, method: str, executable: str, mode: str | None = None
) -> dict[str, Any]:
    component: dict[str, Any] = {
        "state": "available",
        "value": value,
        "units": "degC",
        "method": method,
        "tool_executable": executable,
        "warnings": [],
    }
    if mode is not None:
        component["tool_mode"] = mode
    return component


def _tm(sequence: str, parameters: dict[str, Any]) -> dict[str, Any]:
    value = _number(
        [
            "oligotm",
            *_shared_arguments(parameters),
            "-tp",
            "1",
            "-sc",
            "1",
            sequence,
        ]
    )
    return _component(
        value,
        method="primer3.santalucia_1998.nearest_neighbor",
        executable="oligotm",
    )


def _thal(
    sequence_1: str,
    sequence_2: str | None,
    mode: str,
    parameters: dict[str, Any],
) -> dict[str, Any]:
    arguments = [
        "ntthal",
        "-r",
        "-a",
        mode,
        *_shared_arguments(parameters),
        "-maxloop",
        str(parameters["max_loop"]),
        "-s1",
        sequence_1,
    ]
    if sequence_2 is not None:
        arguments.extend(["-s2", sequence_2])
    value = _number(arguments)
    methods = {
        "HAIRPIN": "primer3.ntthal.hairpin",
        "ANY": "primer3.ntthal.any_complementarity",
        "END1": "primer3.ntthal.three_prime_end_complementarity",
    }
    return _component(value, method=methods[mode], executable="ntthal", mode=mode)


def _individual(sequence: str, parameters: dict[str, Any]) -> dict[str, Any]:
    normalized = "".join(sequence.split()).upper()
    if not _UNAMBIGUOUS_DNA.fullmatch(normalized):
        raise ScientificToolError(
            "unsupported_sequence", "Primer3 requires unambiguous A/C/G/T DNA."
        )
    if len(normalized) > int(parameters["max_nn_length"]):
        raise ScientificToolError(
            "sequence_too_long", "Sequence exceeds the qualified nearest-neighbor limit."
        )
    return {
        "nearest_neighbor_tm": _tm(normalized, parameters),
        "hairpin": _thal(normalized, None, "HAIRPIN", parameters),
        "homodimer": _thal(normalized, normalized, "ANY", parameters),
    }


def primer3_analysis(
    kind: str, input_snapshot: dict[str, Any], parameters: dict[str, Any]
) -> dict[str, Any]:
    """Return reproducible thermodynamic facts without biological interpretation."""
    tool_version = _tool_version()
    started_at = datetime.now(UTC)
    if kind == "oligo_primer3_qc":
        payload = _individual(input_snapshot["sequence"]["normalized"], parameters)
    elif kind == "assay_primer3_pair_compatibility":
        forward_sequence = input_snapshot["forward"]["normalized_sequence"]
        reverse_sequence = input_snapshot["reverse"]["normalized_sequence"]
        forward = _individual(forward_sequence, parameters)
        reverse = _individual(reverse_sequence, parameters)
        tm_delta = abs(
            float(forward["nearest_neighbor_tm"]["value"])
            - float(reverse["nearest_neighbor_tm"]["value"])
        )
        payload = {
            "forward": forward,
            "reverse": reverse,
            "tm_delta": _component(
                tm_delta,
                method="derived.absolute_primer3_tm_delta",
                executable="oligospace_bioinfo",
            ),
            "heterodimer": _thal(forward_sequence, reverse_sequence, "ANY", parameters),
            "end_complementarity": _thal(forward_sequence, reverse_sequence, "END1", parameters),
        }
    else:
        raise ScientificToolError("unsupported_job_kind", "The scientific job kind is unsupported.")
    completed_at = datetime.now(UTC)
    return {
        "payload": payload,
        "warnings": [],
        "provenance": {
            "algorithm": "Primer3 thermodynamic analysis",
            "tool": "Primer3",
            "tool_version": tool_version,
            "tool_source_sha256": PRIMER3_SOURCE_SHA256,
            "worker_version": __version__,
            "wrapper_contract_version": WRAPPER_CONTRACT_VERSION,
            "build_identity": os.environ.get("OLIGOSPACE_BUILD_ID", "development-unpinned"),
            "parameters": parameters,
            "started_at": started_at,
            "completed_at": completed_at,
        },
        "interpretation": None,
    }


def _claim(job_id: str, claim_token: str, task_id: str | None) -> dict[str, Any] | None:
    now = datetime.now(UTC)
    lease = now + timedelta(seconds=_lease_seconds())
    with (
        psycopg.connect(_database_url(), row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute("SELECT * FROM scientific_jobs WHERE id = %s FOR UPDATE", (job_id,))
        job = cursor.fetchone()
        if job is None or job["state"] not in ("queued", "retrying"):
            return None
        if job["claim_token"] != claim_token or job["attempt_count"] >= job["max_attempts"]:
            return None
        attempt_number = int(job["attempt_count"]) + 1
        attempt_id = uuid.uuid4()
        cursor.execute(
            """UPDATE scientific_jobs SET state='running', attempt_count=%s,
                   started_at=COALESCE(started_at, %s), updated_at=%s,
                   last_error_code=NULL, last_error_summary=NULL WHERE id=%s""",
            (attempt_number, now, now, job_id),
        )
        cursor.execute(
            """INSERT INTO scientific_job_attempts
                   (id, job_id, attempt_number, state, task_id, claim_token, claimed_at,
                    lease_expires_at, started_at, retryable, diagnostics)
                   VALUES (%s,%s,%s,'running',%s,%s,%s,%s,%s,false,%s)""",
            (
                attempt_id,
                job_id,
                attempt_number,
                task_id,
                claim_token,
                now,
                lease,
                now,
                Jsonb({}),
            ),
        )
        job["attempt_id"] = attempt_id
        job["attempt_number"] = attempt_number
        return job


def _lock_current_attempt(cursor: Any, job: dict[str, Any], now: datetime) -> bool:
    """Lock the job and attempt; reject completion from a superseded attempt."""
    cursor.execute(
        "SELECT state, attempt_count FROM scientific_jobs WHERE id=%s FOR UPDATE", (job["id"],)
    )
    job_row = cursor.fetchone()
    cursor.execute(
        "SELECT state FROM scientific_job_attempts WHERE id=%s FOR UPDATE", (job["attempt_id"],)
    )
    attempt_row = cursor.fetchone()
    attempt_state = None if attempt_row is None else attempt_row[0]
    if (
        job_row is not None
        and job_row[0] == "running"
        and int(job_row[1]) == int(job["attempt_number"])
        and attempt_state == "running"
    ):
        return True
    if attempt_state == "running":
        cursor.execute(
            """UPDATE scientific_job_attempts SET state='failed', completed_at=%s,
                   retryable=false, error_code='stale_attempt',
                   error_summary='Attempt superseded before completion.' WHERE id=%s""",
            (now, job["attempt_id"]),
        )
    cursor.execute(
        """INSERT INTO audit_events
               (id, occurred_at, actor_id, action, entity_type, entity_id, before, after)
               VALUES (%s,%s,NULL,'stale_attempt_rejected','scientific_job',%s,%s,%s)""",
        (
            uuid.uuid4(),
            now,
            job["id"],
            Jsonb(
                {
                    "state": None if job_row is None else job_row[0],
                    "attempt_count": None if job_row is None else job_row[1],
                }
            ),
            Jsonb({"attempt_number": job["attempt_number"], "attempt_state": attempt_state}),
        ),
    )
    return False


def _succeed(job: dict[str, Any], analysis: dict[str, Any]) -> bool:
    provenance = analysis["provenance"]
    now = datetime.now(UTC)
    with psycopg.connect(_database_url()) as connection, connection.cursor() as cursor:
        if not _lock_current_attempt(cursor, job, now):
            return False
        cursor.execute(
            """INSERT INTO scientific_job_results
                   (job_id, result_schema_version, payload, warnings, algorithm, tool_version,
                    tool_source_sha256,
                    worker_version, wrapper_contract_version, build_identity, started_at,
                    completed_at, executed_at)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                job["id"],
                RESULT_SCHEMA_VERSION,
                Jsonb(analysis["payload"]),
                Jsonb(analysis["warnings"]),
                provenance["algorithm"],
                provenance["tool_version"],
                provenance["tool_source_sha256"],
                provenance["worker_version"],
                provenance["wrapper_contract_version"],
                provenance["build_identity"],
                provenance["started_at"],
                provenance["completed_at"],
                now,
            ),
        )
        cursor.execute(
            """UPDATE scientific_job_attempts SET state='succeeded', completed_at=%s,
                   tool_version=%s, worker_version=%s, wrapper_contract_version=%s,
                   build_identity=%s, exit_status=0 WHERE id=%s""",
            (
                now,
                provenance["tool_version"],
                provenance["worker_version"],
                provenance["wrapper_contract_version"],
                provenance["build_identity"],
                job["attempt_id"],
            ),
        )
        cursor.execute(
            """UPDATE scientific_jobs SET state='succeeded', completed_at=%s,
                   updated_at=%s WHERE id=%s""",
            (now, now, job["id"]),
        )
        cursor.execute(
            """INSERT INTO audit_events
                   (id, occurred_at, actor_id, action, entity_type, entity_id, before, after)
                   VALUES (%s,%s,NULL,'succeed','scientific_job',%s,%s,%s)""",
            (
                uuid.uuid4(),
                now,
                job["id"],
                Jsonb({"state": "running", "attempt_number": job["attempt_number"]}),
                Jsonb({"state": "succeeded", "public_id": job["public_id"]}),
            ),
        )
    return True


def _fail(job: dict[str, Any], error: ScientificToolError) -> str:
    now = datetime.now(UTC)
    retrying = error.retryable and int(job["attempt_number"]) < int(job["max_attempts"])
    state = "retrying" if retrying else "failed"
    next_retry = (
        now + timedelta(seconds=min(60, 2 ** int(job["attempt_number"]))) if retrying else None
    )
    with psycopg.connect(_database_url()) as connection, connection.cursor() as cursor:
        if not _lock_current_attempt(cursor, job, now):
            return "stale"
        cursor.execute(
            """UPDATE scientific_job_attempts SET state='failed', completed_at=%s,
                   retryable=%s, error_code=%s, error_summary=%s WHERE id=%s""",
            (
                now,
                error.retryable,
                error.code,
                error.summary[:500],
                job["attempt_id"],
            ),
        )
        cursor.execute(
            """UPDATE scientific_jobs SET state=%s, next_retry_at=%s, completed_at=%s,
                   last_error_code=%s, last_error_summary=%s, updated_at=%s WHERE id=%s""",
            (
                state,
                next_retry,
                None if retrying else now,
                error.code,
                error.summary[:500],
                now,
                job["id"],
            ),
        )
        cursor.execute(
            """INSERT INTO audit_events
                   (id, occurred_at, actor_id, action, entity_type, entity_id, before, after)
                   VALUES (%s,%s,NULL,%s,'scientific_job',%s,%s,%s)""",
            (
                uuid.uuid4(),
                now,
                "retry_scheduled" if retrying else "fail",
                job["id"],
                Jsonb({"state": "running", "attempt_number": job["attempt_number"]}),
                Jsonb({"state": state, "error_code": error.code}),
            ),
        )
    return state


@app.task(bind=True, name="oligospace.scientific_job", max_retries=2)  # type: ignore[misc]
def scientific_job_task(self: Task, job_id: str, claim_token: str) -> dict[str, Any]:
    try:
        job = _claim(job_id, claim_token, self.request.id)
    except psycopg.OperationalError as exc:
        raise self.retry(exc=exc, countdown=5) from exc
    if job is None:
        return {"state": "noop", "job_id": job_id}
    deadline = _attempt_deadline.set(
        time.monotonic() + _lease_seconds() - LEASE_SAFETY_MARGIN_SECONDS
    )
    try:
        analysis = primer3_analysis(job["kind"], job["input_snapshot"], job["effective_parameters"])
        if not _succeed(job, analysis):
            return {"state": "stale_attempt_rejected", "job_id": job_id}
        return {"state": "succeeded", "job_id": job_id}
    except ScientificToolError as exc:
        outcome = _fail(job, exc)
        if outcome == "stale":
            return {"state": "stale_attempt_rejected", "job_id": job_id}
        if outcome == "retrying":
            countdown = min(60, 2 ** int(job["attempt_number"]))
            raise self.retry(exc=exc, countdown=countdown) from exc
        return {"state": "failed", "job_id": job_id, "error_code": exc.code}
    except Exception:
        _fail(job, ScientificToolError("worker_error", "The worker failed safely."))
        raise
    finally:
        _attempt_deadline.reset(deadline)


@app.task(name="oligospace.reconcile_scientific_jobs")  # type: ignore[misc]
def reconcile_scientific_jobs() -> dict[str, int]:
    now = datetime.now(UTC)
    dispatched = 0
    recovered = 0
    with (
        psycopg.connect(_database_url(), row_factory=dict_row) as connection,
        connection.cursor() as cursor,
    ):
        cursor.execute(
            """SELECT id, claim_token FROM scientific_jobs
                   WHERE (state='queued' AND queued_at < %s)
                      OR (state='retrying' AND next_retry_at <= %s)
                   ORDER BY created_at LIMIT 100 FOR UPDATE SKIP LOCKED""",
            (now - timedelta(seconds=30), now),
        )
        due = cursor.fetchall()
        cursor.execute(
            """SELECT j.id, j.attempt_count, j.max_attempts, j.claim_token,
                          a.id AS attempt_id
                   FROM scientific_jobs j JOIN scientific_job_attempts a ON a.job_id=j.id
                   WHERE j.state='running' AND a.state='running' AND a.lease_expires_at < %s
                   FOR UPDATE OF j, a SKIP LOCKED""",
            (now,),
        )
        for expired in cursor.fetchall():
            retrying = expired["attempt_count"] < expired["max_attempts"]
            state = "retrying" if retrying else "failed"
            cursor.execute(
                """UPDATE scientific_job_attempts SET state='failed', completed_at=%s,
                       retryable=true, error_code='worker_lost',
                       error_summary='Worker lease expired.' WHERE id=%s""",
                (now, expired["attempt_id"]),
            )
            cursor.execute(
                """UPDATE scientific_jobs SET state=%s, next_retry_at=%s,
                       completed_at=%s, last_error_code='worker_lost',
                       last_error_summary='Worker lease expired.', updated_at=%s WHERE id=%s""",
                (
                    state,
                    now if retrying else None,
                    None if retrying else now,
                    now,
                    expired["id"],
                ),
            )
            cursor.execute(
                """INSERT INTO audit_events
                       (id, occurred_at, actor_id, action, entity_type, entity_id, before, after)
                       VALUES (%s,%s,NULL,'worker_lost','scientific_job',%s,%s,%s)""",
                (
                    uuid.uuid4(),
                    now,
                    expired["id"],
                    Jsonb({"state": "running", "attempt_number": expired["attempt_count"]}),
                    Jsonb({"state": state, "error_code": "worker_lost"}),
                ),
            )
            if retrying:
                due.append(expired)
            recovered += 1
    for job in due:
        result = app.send_task(
            "oligospace.scientific_job", args=[str(job["id"]), job["claim_token"]]
        )
        _record_redispatch(job["id"], str(result.id))
        dispatched += 1
    return {"dispatched": dispatched, "recovered": recovered}


def _record_redispatch(job_id: Any, task_id: str) -> None:
    now = datetime.now(UTC)
    with psycopg.connect(_database_url()) as connection, connection.cursor() as cursor:
        cursor.execute(
            "UPDATE scientific_jobs SET celery_task_id=%s, updated_at=%s WHERE id=%s",
            (task_id, now, job_id),
        )
        cursor.execute(
            """INSERT INTO audit_events
                   (id, occurred_at, actor_id, action, entity_type, entity_id, before, after)
                   VALUES (%s,%s,NULL,'redispatch','scientific_job',%s,%s,%s)""",
            (uuid.uuid4(), now, job_id, Jsonb({}), Jsonb({"celery_task_id": task_id})),
        )


def primer3_qc(sequence: str, **parameters: float) -> dict[str, Any]:
    """Backward-compatible Plan-001 wrapper with explicit Primer3 provenance."""
    effective: dict[str, Any] = {
        "mv_conc_mM": parameters.get("mv_conc", 50.0),
        "dv_conc_mM": parameters.get("dv_conc", 1.5),
        "dntp_conc_mM": parameters.get("dntp_conc", 0.6),
        "dna_conc_nM": parameters.get("dna_conc", 50.0),
        "max_loop": 30,
        "max_nn_length": 60,
        "tm_method": "santalucia_1998",
        "salt_correction_method": "santalucia_1998",
    }
    snapshot = {"sequence": {"normalized": "".join(sequence.split()).upper()}}
    result = primer3_analysis("oligo_primer3_qc", snapshot, effective)
    payload = result["payload"]
    return {
        "input": {"normalized_sequence": snapshot["sequence"]["normalized"]},
        "result": {
            "tm_c": payload["nearest_neighbor_tm"]["value"],
            "hairpin_tm_c": payload["hairpin"]["value"],
            "homodimer_tm_c": payload["homodimer"]["value"],
        },
        "provenance": result["provenance"],
        "interpretation": None,
    }


@app.task(name="oligospace.primer3_qc")  # type: ignore[misc]
def primer3_qc_task(sequence: str, parameters: dict[str, float] | None = None) -> dict[str, Any]:
    return primer3_qc(sequence, **(parameters or {}))
