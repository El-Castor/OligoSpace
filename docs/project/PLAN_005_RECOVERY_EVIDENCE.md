# Plan 005 — interruption and recovery evidence

- Date: 2026-10-29
- Branch: `codex/scientific-jobs-primer3` (base commit `529fc2d`, fixes committed locally
  afterwards, not pushed)
- Stack: Compose project `oligospace-e2e` only (`compose.yml` + `compose.e2e.yml`,
  `infra/e2e/e2e.env`). This project declares no named volumes. The development stack
  (`oligospace`) was not restarted, stopped or modified, and its volumes were not touched.
- Worker: Celery prefork, concurrency 4, prefetch 1, `acks_late`. Beat
  (`scientific-scheduler`) triggers `oligospace.reconcile_scientific_jobs` every 30 s.
  Maximum of 3 attempts per job.
- Evidence sources: PostgreSQL (`scientific_jobs`, `scientific_job_attempts`,
  `scientific_job_results`, `audit_events`), worker/scheduler logs and the HTTP API
  responses. An HTTP 200/202 response alone was never treated as a validation.

## Two different guarantees

| Guarantee | Owner | Observed behaviour |
|---|---|---|
| Durable job history (state, attempts, results, audit) | PostgreSQL | Kept in full across worker kill and Redis restart. It is the authoritative source; reconciliation rebuilds work from it. |
| Persistence of queue messages and Celery results | Redis broker/backend | **Not guaranteed.** A Redis restart dropped `DBSIZE` from 18 to 3. Queued messages and Celery result keys were lost. |

Recovery therefore never depends on Redis keeping a message. The reconcile task re-dispatches
`queued`/`retrying` jobs whose dispatch is missing or overdue, and moves `running` attempts
with an expired lease to `failed/worker_lost`. Losing a Redis message can delay a job but
cannot lose an authoritative result.

## Scenario A — worker killed during execution: PASS

Job `SJOB-000001`.

| Time (UTC) | Event |
|---|---|
| 10:09:29.549 | submit → `queued`; attempt 1 starts at 10:09:29.584 (lease to 10:11:29) |
| 10:09:50 | worker container SIGKILLed while attempt 1 was running |
| 10:11:57.711 | reconcile returns `{dispatched: 1, recovered: 1}`; attempt 1 → `failed/worker_lost` (10:11:57.712) |
| 10:11:57.737 | attempt 2 starts |
| 10:11:57.750 | attempt 2 `succeeded`; job `succeeded` |

Result: exactly 1 result row, no concurrent execution (attempt 1's process had died). This
run predates the audit-event fix, so it has no `worker_lost`/`redispatch` audit rows and the
job's `celery_task_id` still names attempt 1's task. Scenario C covers both points after the
fix.

## Scenario B1 — Redis restart after completion: PASS

Job `SJOB-000002`: submitted at 10:13:23.290 and succeeded at 10:13:23.310 (1 attempt).
Redis was restarted at 10:13:34. `DBSIZE` went from 18 to 3, so Celery result keys and
messages were lost. The PostgreSQL job, attempt, result and audit rows were unchanged
afterwards, and the API still returned the result.

## Scenario B2 — Redis unavailable at submission: PASS

Job `SJOB-000003`.

| Time (UTC) | Event |
|---|---|
| 10:14:57.940 | Redis stopped |
| 10:14:58.255 | submit audit; job persisted as `queued` |
| 10:15:17.351 | audit `dispatch_failed` |
| 10:15:17.380 | API returns **503** (job kept, not lost) |
| — | idempotent replay of the same request returns **200** with the same job (no duplicate) |
| — | Redis started again |
| 10:15:29.193 | reconcile `dispatched: 1`; attempt 1 starts |
| 10:15:29.205 | job `succeeded` |

Result: 1 job and 1 result. Pre-fix limitation: `celery_task_id` stayed NULL and there was no
`redispatch` audit row.

## Scenario C — stuck job reconciliation

A fault wrapper made `oligotm` sleep 40 s on its first calls, with a 10 s lease, so
reconcile would see an expired lease while the original attempt was still alive.

### C0 — before the fix: DEFECT

Job `SJOB-000004`.

| Time (UTC) | Event |
|---|---|
| 10:23:33.450 | attempt 1 claims (lease to 10:23:43) |
| 10:23:48.702 | reconcile marks attempt 1 `worker_lost`; attempt 2 starts |
| 10:24:13.477 | **stale attempt 1 commits success** |

Final state was inconsistent: attempt 1 was `succeeded` with `error_code=worker_lost`,
attempt 2 stayed `running`, and the job was `succeeded`. Only the `scientific_job_results`
primary key (job_id) prevented a second result row. Two executions also overlapped.

### Fix 1 — attempt fencing (`services/bioinfo-worker/src/oligospace_bioinfo/tasks.py`)

- `_lock_current_attempt` locks the job and attempt rows `FOR UPDATE`. A result or failure is
  committed only if the attempt is still `running` and is the job's current attempt.
- A superseded attempt does not change the job. A stale `running` row is closed as
  `failed/stale_attempt`, and the rejection is audited as `stale_attempt_rejected`.
  `_succeed` returns `False` and `_fail` returns `"stale"` (no retry is scheduled).
- Reconcile locks with `SKIP LOCKED`, audits `worker_lost` and `redispatch`, and records the
  new Celery task id.

### C1 — fencing only: PASS, residual overlap

Job `SJOB-000005` (`87ec2ceb-b45e-4590-a2bb-4565dc9f13c6`).

| Time (UTC) | Event |
|---|---|
| 10:30:17.574 | submit 202 |
| 10:30:17.678 | attempt 1 starts (lease to 10:30:27) |
| 10:30:32.919 | reconcile `{1, 1}`; audit `worker_lost`; attempt 1 → `failed/worker_lost` |
| 10:30:32.933 | audit `redispatch` |
| 10:30:32.934 | attempt 2 starts |
| 10:30:57.698 | attempt 1 returns; audit `stale_attempt_rejected`, nothing written |
| 10:31:12.960 | attempt 2 `succeeded` |

The transitions were consistent and there was 1 result. However, the attempt 1 and attempt 2
subprocesses still ran at the same time, because the tool timeout (30 s) was longer than the
lease.

### Fix 2 — tool timeout bounded by the lease

The attempt deadline is the lease minus 5 s, held in the `_attempt_deadline` ContextVar.
`_tool_timeout()` uses the smaller of `SCIENTIFIC_TOOL_TIMEOUT_SECONDS` and the remaining
lease. `_run_tool` refuses to start the tool when the lease is exhausted, raising the
retryable `lease_exhausted` error. A tool therefore ends before reconcile can treat its
attempt as lost.

### C2 — fencing and deadline: PASS

Job `SJOB-000006` (`1f88b874-55e7-4b21-bf03-33a338347fb3`), submit 202 at 10:36:53.419.

| Attempt | Start | End | Lease to | Outcome |
|---|---|---|---|---|
| 1 | 10:36:53.533 | 10:36:58.549 | 10:37:03 | `failed/tool_timeout` (retryable) |
| 2 | 10:37:00.565 | 10:37:05.591 | 10:37:10 | `failed/tool_timeout` (retryable) |
| 3 | 10:37:09.618 | 10:37:09.640 | 10:37:19 | `succeeded` |

Audit: `submit`, `retry_scheduled` ×2, `succeed`. The reconcile triggered at 10:37:08.583 (task `ac03e200…`) returned
`{dispatched: 0, recovered: 0}`: no attempt was stale, nothing was recovered, and no attempts
overlapped. The job reached an explicit terminal state with `attempt_count = 3` and 1 result.

### Totals across the six jobs

All six jobs ended `succeeded` with exactly one `scientific_job_results` row each. No result
was lost or duplicated. The only inconsistent transition (C0) was fixed and re-tested (C1,
C2).

## Regression tests

`services/bioinfo-worker/tests/test_attempt_fencing.py` (7 tests):

- the current attempt commits;
- a superseded attempt cannot succeed and is audited;
- a stale `running` row is closed without touching the job;
- a superseded failure does not schedule a retry;
- a current failure reports a retry;
- the tool timeout is bounded by the lease;
- an exhausted lease stops before the tool runs.

## Gates after the fixes (2026-10-29)

| Gate | Result |
|---|---|
| `make PYTHON_RUNNER=container format` / `lint` / `typecheck` | exit 0 |
| `make PYTHON_RUNNER=container test` | API 25 passed / 7 skipped; worker 14 passed; web 2 passed |
| `make PYTHON_RUNNER=container test-integration` | 7 passed (PostgreSQL, Alembic round-trip) |
| `make test-e2e` (`oligospace-e2e`, Caddy) | 10 passed in 14.3 s |
| `make compose-config` | OK |
| GitHub CI | green on `f7fff83` and `975a8ae`; `529fc2d` and the fixes are not pushed, so they have no CI run yet |

## Residual risks (not blocking Plan 005)

- **No lease heartbeat or renewal.** An attempt that blocks outside the tool subprocess (for
  example on DB I/O) can outlive its lease and overlap with a new attempt. Fencing still
  keeps the result correct, but the work is duplicated.
- A short lease combined with the 30 s Beat cadence causes retry churn. A lease of 5 s or
  less yields an immediate `lease_exhausted`. The default lease (120 s) and timeout (30 s)
  are safe.
- The claim token is not rotated per attempt; retries reuse the Celery `task_id`.
- Scenarios A and B2 ran before the audit-event fix, so they lack `worker_lost`/`redispatch`
  rows. C1 shows the fixed behaviour.
- Whether the fault wrapper's `sleep` child was reaped inside the container was not verified
  (`ps` is unavailable in the image). This only matters for the test harness.
- mypy reports errors on monkeypatches in the worker tests that existed before this work.
- A local-execution runbook is not written yet.

## Runbook — stuck scientific job

1. Identify the job: `state` in `queued`/`retrying`/`running`, with its latest attempt and
   `lease_expires_at` (tables `scientific_jobs` and `scientific_job_attempts`).
2. Do not edit rows by hand. Reconcile runs every 30 s. It recovers expired `running`
   attempts as `failed/worker_lost` and re-dispatches `queued`/`retrying` jobs that are
   missing from Redis. Check the worker logs for
   `oligospace.reconcile_scientific_jobs ... {'dispatched': n, 'recovered': m}`.
3. Check the audit trail: `worker_lost`, `redispatch`, `retry_scheduled`,
   `stale_attempt_rejected`, `dispatch_failed`.
4. When `max_attempts` is reached, the job ends `failed` with the last `error_code`. This is
   an explicit terminal state: resubmit rather than mutating the job.
5. If Redis was restarted or flushed, no action is required: PostgreSQL holds the job and
   reconcile re-dispatches it. Expect only a delay.
6. Never run `docker compose down -v` without first checking the project name and its
   volumes.
