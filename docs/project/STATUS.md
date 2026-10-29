# Project status

Last updated: 2026-10-29

## Current phase

Execution plans 001 through 004 are complete. Plan 004 added experiment runs,
contextual validation, and quarantined evidence attachments. The development
application is a usable multi-user registry through Caddy. Execution plan 005,
Persistent scientific jobs and Primer3 analysis, is approved, active, and in progress.
Its first increment covers individual Oligo QC and Forward/Reverse
Assay pair analysis. No production deployment exists.

## Build verified

- FastAPI identity/workspace administration, explicit membership-aware RBAC,
  scope validation, audit events, reversible Alembic revision `0002`, and the
  deterministic administrator/researcher seed pass formatting, lint, and strict
  typing.
- The Next.js login, profile, personalized dashboard, team/project/admin pages,
  user menu/logout, project-aware forms, and project search pass ESLint,
  TypeScript, unit checks, and the production build.
- Production API/web images build successfully. Primer3 2.6.1 compiles and BLAST+
  2.17.0 downloads with its pinned checksum. Build success alone is not treated as
  browser functionality.
- ExperimentRun, Validation, Attachment, private MinIO integration, migration `0003`,
  evidence search, dashboard attention count, and their Next.js workflows pass the
  repository format, lint, strict typing, unit-test, and production-image gates.

## API and PostgreSQL verified

- `make test-integration` migrates a guaranteed-fresh PostgreSQL 17 database from
  `0001` through `0004`, round-trips Alembic (head → `0003_experiment_evidence` →
  head), and passes seven integration tests with zero skips enforced by
  `OLIGOSPACE_REQUIRE_INTEGRATION=1`. The CI `integration` job runs the same target.
- The core registry round trip still verifies Oligo/Target/Assay creation,
  immutable biological identity, duplicate rejection, contextual roles,
  versioning, authorization, and audit evidence.
- Workspace integration verifies real users, profile persistence, Team and Project
  membership, Private/Project/Team/Institute visibility, inactive-account
  rejection, member/admin boundaries, project persistence, and audit events.
- The integration target now removes stale test PostgreSQL containers before and
  after every run so interrupted runs cannot contaminate later evidence.
- Repeated ExperimentRuns preserve the Assay version snapshot. Contextual Validation
  supersession retains prior conclusions; bounded attachment upload, SHA-256,
  quarantine, soft removal, authorization, audit, dashboard counts, and transaction
  reload persistence are verified against PostgreSQL.

## Service runtime verified

- Caddy, production Next.js, FastAPI, PostgreSQL, MinIO, migrations, and deterministic
  seeds start through the health-gated Compose path.
- Host HTTP smoke on `http://oligospace.localhost:8080` returns the expected root
  login redirect, a successful login page, and `{"status":"ok"}` from
  `/api/v1/health/live`.
- Keycloak starts and the OIDC/token-refresh configuration is implemented, but the
  institutional production OIDC journey is not browser-verified.

## Browser/E2E verified

- `make test-e2e` passes 10 Chromium tests in 8 spec files through Caddy: smoke and
  personalized dashboard; development login/profile/logout/second identity;
  Oligo; Target; Assay plus global search; Project/Team/Admin workflows; evidence;
  and scientific jobs. It runs in the isolated `oligospace-e2e` Compose project
  (tmpfs storage, no host port, public placeholders from `infra/e2e/e2e.env`, never
  reads `.env`) that is torn down after every run.
- The browser workflows prove UI → API → PostgreSQL → browser reload persistence,
  Forward/Reverse Oligo association, project membership, normal-user admin denial,
  and session return login.
- A separate Chromium smoke using host networking passes against
  `http://oligospace.localhost:8080`, in addition to the Compose E2E journey.
- These statements apply to development authentication. Production Keycloak login
  remains implemented but not browser-verified.
- The seventh spec verifies ExperimentRun create/detail, a second run, real MinIO
  evidence upload and quarantine display, contextual Validation, supersession,
  ExperimentType guidance, evidence-aware global search, awaiting-validation
  dashboard rendering, and persistence after browser reload.

## In progress / incomplete

- Plan 005 has implemented its qualified Primer3 contract, migration 0004, persistent
  job/attempt/result core, API/queue/worker/reconciliation path, and both browser
  workflows. Unit, worker, PostgreSQL integration, production image, service runtime,
  and Caddy HTTP smoke gates pass. Browser Playwright for both scientific-job
  workflows passes in the isolated E2E stack (2026-10-29). Interruption/recovery
  gates remain pending, so the plan is not yet complete.
- Inventory/orders/QR, reference ingestion,
  GeneOligoViewer, complete catalogue/inventory search,
  production backup execution, monitoring, and hardening remain later work.
- Stock values remain explicitly unavailable; no scientific or operational values
  are invented. Attachment malware scanning is not integrated, so all uploads remain
  private/quarantined with no publication or download path.

## Blockers and required inputs

- Institutional hostname/SSO/LDAP, INRAE backup endpoint and retention approval,
  production secrets, and governed reference FASTA/GFF data are not supplied.

## Known technical debt

- PostgreSQL RLS remains defense-in-depth work after the application permission
  policy and a safe per-request database security context are stabilized.
- Synchronous API Tm remains the explicitly labeled Wallace screening method;
  Primer3 nearest-neighbor and structure facts use separate persistent job records.
- OIDC needs an institutional browser validation with real production-like realm
  policy, token refresh, logout, and disabled-account lifecycle.
- ESLint 9 remains pinned until the Next.js plugin dependency graph accepts ESLint 10.

## Last validated commands

All on 2026-10-29 via `PYTHON_RUNNER=container` unless noted:

- `make format lint typecheck` — passed (Ruff, mypy, ESLint, TypeScript).
- `make test` — passed: API 25 passed, 7 skipped (PostgreSQL tests delegated to
  `make test-integration`); bioinfo worker 7 passed; web 2 passed, 0 skipped.
- `make test-integration` — passed: 7 passed, 0 skipped; Alembic round-trip OK;
  fresh test container removed after execution.
- `make test-e2e` — passed: 10 passed, 0 failed, 0 skipped in 17.9 s in the
  isolated `oligospace-e2e` project. Dev database row counts, containers, volumes,
  and images were identical before and after the run.
- `make compose-config` — passed for the dev and E2E configurations.
- GitHub CI on `f7fff83` — backend, frontend, bioinfo-worker, migration,
  integration, and compose jobs succeeded.
- Host-network Chromium smoke (2026-09-07) — passed: 1 smoke spec at
  `http://oligospace.localhost:8080`.
- Host HTTP smoke (2026-09-07) — root `307` to login, login `200`, health
  `200`/`status: ok`.

Database migration: `0004_scientific_jobs` is applied to the development PostgreSQL
database (observed) and to a fresh isolated PostgreSQL 17 database, including the
downgrade/upgrade round-trip.
