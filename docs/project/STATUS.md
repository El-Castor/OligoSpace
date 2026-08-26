# Project status

Last updated: 2026-08-26

## Current phase

Phase 0 audit/documentation and the Phase 1 foundation are complete under execution
plan 001. The next implementation plan has not been activated; no production
deployment exists.

## Working

- Source workbook located and inspected read-only; a mid-audit external file change
  is captured with both checksums, and the current importer preview finds 93
  importable candidates plus seven rejected invalid/example sequences.
- Architecture, model, security, deployment, backup, bioinformatics, and UI
  direction documented.
- Core FastAPI registry endpoints, explicit RBAC/visibility policy, audit events,
  SQLAlchemy models, reversible Alembic migration, and deterministic seed exist.
- Next.js scientific workspace, OIDC boundary, Compose stack, CI, and production
  application images build successfully.
- The Celery worker runs checksum-pinned Primer3 2.6.1 thermodynamic calculations;
  BLAST+ 2.17.0 is installed and version-checked for later reference-backed work.

## In progress / incomplete

- ExperimentRun/Validation, inventory/orders/QR, attachments, search, gene viewer,
  API-to-worker job persistence, production backup execution, monitoring, and
  hardening remain.

## Blockers and required inputs

- Institutional hostname/SSO/LDAP, INRAE backup endpoint and retention approval,
  production secrets, and reference FASTA/GFF data are not supplied.

## Known technical debt

- PostgreSQL RLS and integration tests follow stabilization of permission policy.
- Synchronous API Tm remains the explicitly labeled Wallace screening method; the
  worker's Primer3 result is not yet persisted or exposed through an API job.
- ESLint 9 is pinned because the Next.js 16 plugin dependency graph does not yet
  accept ESLint 10.

## Last validated commands

- `make format PYTHON_RUNNER=container` — passed 2026-08-26.
- `make lint typecheck test PYTHON_RUNNER=container` — passed: 15 API tests,
  2 worker tests, web smoke test, strict Python/TypeScript checks.
- `make compose-config` and `docker compose build api web bioinfo-worker` — passed.
- Isolated PostgreSQL migration/seed — revision `0001_initial_registry`, 17 seeded
  experiment types; temporary validation volume removed.
- Read-only Excel preview — 93 importable, 7 rejected, 359 allocated-only, 0
  imported; source SHA-256 unchanged before and after preview.

Database migration: `0001_initial_registry` created and applied successfully to
PostgreSQL 17 during isolated validation.
