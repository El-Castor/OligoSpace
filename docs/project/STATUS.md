# Project status

Last updated: 2026-09-02

## Current phase

Execution plans 001 (foundation), 002 (core registry), and 003 (identity, users,
workspaces, and administration) are complete. The development application is a
usable multi-user core registry through Caddy. No later execution plan is active
and no production deployment exists.

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

## API and PostgreSQL verified

- `make test-integration` migrates a guaranteed-fresh PostgreSQL 17 database from
  `0001` through `0002` and passes three integration tests.
- The core registry round trip still verifies Oligo/Target/Assay creation,
  immutable biological identity, duplicate rejection, contextual roles,
  versioning, authorization, and audit evidence.
- Workspace integration verifies real users, profile persistence, Team and Project
  membership, Private/Project/Team/Institute visibility, inactive-account
  rejection, member/admin boundaries, project persistence, and audit events.
- The integration target now removes stale test PostgreSQL containers before and
  after every run so interrupted runs cannot contaminate later evidence.

## Service runtime verified

- Caddy, production Next.js, FastAPI, PostgreSQL, migrations, and deterministic
  seeds start through the health-gated Compose path.
- Host HTTP smoke on `http://oligospace.localhost:8080` returns the expected root
  login redirect, a successful login page, and `{"status":"ok"}` from
  `/api/v1/health/live`.
- Keycloak starts and the OIDC/token-refresh configuration is implemented, but the
  institutional production OIDC journey is not browser-verified.

## Browser/E2E verified

- `make test-e2e` passes six independent Chromium specs through Caddy: smoke and
  personalized dashboard; development login/profile/logout/second identity;
  Oligo; Target; Assay plus global search; and Project/Team/Admin workflows.
- The browser workflows prove UI → API → PostgreSQL → browser reload persistence,
  Forward/Reverse Oligo association, project membership, normal-user admin denial,
  and session return login.
- A separate Chromium smoke using host networking passes against
  `http://oligospace.localhost:8080`, in addition to the Compose E2E journey.
- These statements apply to development authentication. Production Keycloak login
  remains implemented but not browser-verified.

## In progress / incomplete

- ExperimentRun/Validation, attachments, inventory/orders/QR, reference ingestion,
  GeneOligoViewer, worker-job persistence, complete catalogue/inventory search,
  production backup execution, monitoring, and hardening remain later work.
- Dashboard validation and stock values remain explicit unavailable states; no
  scientific or operational values are invented.

## Blockers and required inputs

- Institutional hostname/SSO/LDAP, INRAE backup endpoint and retention approval,
  production secrets, and governed reference FASTA/GFF data are not supplied.

## Known technical debt

- PostgreSQL RLS remains defense-in-depth work after the application permission
  policy and a safe per-request database security context are stabilized.
- Synchronous API Tm remains the explicitly labeled Wallace screening method; the
  worker's Primer3 result is not yet persisted or exposed through an API job.
- OIDC needs an institutional browser validation with real production-like realm
  policy, token refresh, logout, and disabled-account lifecycle.
- ESLint 9 remains pinned until the Next.js plugin dependency graph accepts ESLint 10.

## Last validated commands

- `make format` via `PYTHON_RUNNER=container` — passed 2026-09-02.
- `make lint typecheck test` via `PYTHON_RUNNER=container` — passed: 19 API
  tests, 3 intentionally skipped integration tests in the unit invocation, 2 real
  Primer3 worker tests, web tests, Ruff, mypy, ESLint, and TypeScript.
- `make compose-config` — passed after the Caddy-network E2E configuration change.
- `make test-integration` — passed: migration `0001` → `0002`, 3 PostgreSQL tests,
  fresh test container removed after execution.
- `make test-e2e` — passed: 6 independent Chromium specs through Caddy.
- Host-network Chromium smoke — passed: 1 smoke spec at
  `http://oligospace.localhost:8080`.
- Host HTTP smoke — root `307` to login, login `200`, health `200`/`status: ok`.

Database migration: `0002_identity_workspaces` is applied successfully to the
development PostgreSQL database and to a fresh isolated PostgreSQL 17 database.
