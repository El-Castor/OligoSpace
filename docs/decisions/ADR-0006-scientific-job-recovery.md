# ADR-0006: PostgreSQL-authoritative scientific jobs with lease-fenced attempts

- Status: accepted
- Date: 2026-10-29

## Context

Scientific jobs (Primer3 via the Celery `bioinfo-worker`) must survive worker crashes and
broker restarts without losing or duplicating results. Plan 005 interruption testing on the
isolated `oligospace-e2e` stack showed that Redis loses queued messages and Celery result keys
on restart, and that a stuck attempt could commit after reconcile had already superseded it
(scenario C0 in `docs/project/PLAN_005_RECOVERY_EVIDENCE.md`).

## Decision

1. **PostgreSQL is authoritative for job state.** `scientific_jobs`,
   `scientific_job_attempts`, `scientific_job_results` and `audit_events` are the only durable
   record. Redis is a transport and is not relied on for durability. A Celery Beat task,
   `oligospace.reconcile_scientific_jobs`, runs every 30 s. It re-dispatches `queued`/`retrying`
   jobs whose dispatch is missing or overdue, and moves `running` attempts whose lease has
   expired to `failed/worker_lost`. Reconcile locks rows with `FOR UPDATE SKIP LOCKED`, audits
   `worker_lost` and `redispatch`, and records the new Celery task id.
2. **Attempts are fenced.** Before an attempt commits a success or a failure, it locks the job
   and attempt rows `FOR UPDATE` (`_lock_current_attempt`). The write happens only if the
   attempt is still `running` and is still the job's current attempt. A superseded attempt
   leaves the job unchanged. Its stale row is closed as `failed/stale_attempt`, the rejection
   is audited as `stale_attempt_rejected`, and no retry is scheduled.
3. **Tool runtime is bounded by the lease.** The attempt deadline is the lease minus
   `LEASE_SAFETY_MARGIN_SECONDS` (5 s). The tool timeout is the smaller of
   `SCIENTIFIC_TOOL_TIMEOUT_SECONDS` and the remaining lease. If the lease is already
   exhausted, the tool is not started and the attempt raises the retryable `lease_exhausted`
   error.

## Alternatives

- **Persistent Redis (AOF) or a durable broker such as RabbitMQ as the source of truth.**
  Rejected: this would add operational weight, and job history would still need to live in
  PostgreSQL for provenance.
- **Relying on the `scientific_job_results` primary key to prevent duplicates.** Rejected: it
  blocks a second result row but still allows inconsistent attempt and job states (C0).
- **Lease heartbeat/renewal.** Deferred. Without it, an attempt blocked outside the tool
  subprocess can outlive its lease. Fencing keeps the outcome correct, but the work is
  duplicated.

## Consequences

- Losing a Redis message can delay a job but cannot lose or duplicate an authoritative result.
- Every recovery transition is auditable.
- A very short lease combined with the 30 s reconcile cadence causes retry churn; a lease of
  5 s or less fails immediately with `lease_exhausted`. The defaults are a 120 s lease and a
  30 s tool timeout.
- Evidence: `docs/project/PLAN_005_RECOVERY_EVIDENCE.md` (scenarios A, B1, B2, C0–C2) and
  `services/bioinfo-worker/tests/test_attempt_fencing.py` (7 tests).
