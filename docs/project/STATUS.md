# Project status

Last updated: 2026-08-26

## Current phase

Phase 0 audit/documentation, the Phase 1 foundation, and the Phase 2 core registry
are complete under execution plans 001 and 002. The core registry is now usable in
the browser through Caddy. No later execution plan has been activated and no
production deployment exists.

## Build verified

- Source workbook located and inspected read-only; a mid-audit external file change
  is captured with both checksums, and the current importer preview finds 93
  importable candidates plus seven rejected invalid/example sequences.
- Architecture, model, security, deployment, backup, bioinformatics, and UI
  direction documented.
- Core FastAPI registry, explicit RBAC/visibility policy, audit events, SQLAlchemy
  models, reversible Alembic migration, and deterministic seed pass static checks.
- Next.js workspace, OIDC boundary, Compose stack, CI, and production application
  images build successfully. This does not establish browser functionality.
- The Celery worker runs checksum-pinned Primer3 2.6.1 thermodynamic calculations;
  BLAST+ 2.17.0 is installed and version-checked for later reference-backed work.

## API and PostgreSQL verified

- The isolated PostgreSQL integration route test migrates a fresh database and
  verifies oligo create/search/detail/metadata update, immutable sequence rejection,
  exact duplicate rejection, target creation, assay creation/versioning, audit
  events, persistence, and a forbidden viewer edit.
- Core API list/create behavior from plan 001 remains covered by unit/static checks;
  plan 002 has added public-ID detail, scoped search, and authorized PATCH routes.

## Service runtime verification

- Isolated PostgreSQL migration and API integration are verified.
- The core development path Caddy → Next.js → FastAPI → PostgreSQL is runtime
  verified with the production web/API images and health-gated Compose startup.
- Keycloak starts on its private network and NextAuth keeps ownership of
  `/api/auth/*`; the interactive OIDC production flow is not yet browser-verified.
- Worker, Redis, and MinIO are not part of the plan 002 browser journey and are not
  claimed as runtime-verified by this milestone.

## Browser workflow verification

- **Verified in development through Caddy on 2026-08-26.** Playwright Chromium
  opens the application root, observes the development identity and dashboard, and
  completes oligo, target, assay, and global-search workflows.
- The journey creates and edits records through the UI, associates Forward and
  Reverse oligos with an assay, reloads the browser, and confirms the same stable
  public records and edited values remain available from PostgreSQL.
- The earlier browser 404 is resolved. Caddy now proxies only `/api/v1/*` to
  FastAPI, leaves `/api/auth/*` to Next.js, dynamically resolves recreated service
  containers, and the standalone Next.js server listens on all container
  interfaces.

## In progress / incomplete

- ExperimentRun/Validation, inventory/orders/QR, attachments, full-catalog search,
  gene viewer,
  API-to-worker job persistence, production backup execution, monitoring, and
  hardening remain. Core-only search is complete; projects, inventory, and later
  catalogue domains are not yet included in global search.

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
- `make test-integration` — passed 2026-08-26 against an isolated PostgreSQL 17
  database after applying `0001_initial_registry`.
- `make test-e2e` — passed 2026-08-26: Playwright Chromium, 1 complete core-registry
  journey through Caddy, including persistence after browser reload.
- `docker compose up --build --detach caddy` — production web/API images built and
  the core service path passed its health gates before the E2E journey.

Database migration: `0001_initial_registry` created and applied successfully to
PostgreSQL 17 during isolated validation.
