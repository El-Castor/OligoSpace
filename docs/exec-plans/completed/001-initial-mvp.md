# Execution plan 001: Initial MVP

- Status: completed
- Started: 2026-08-25
- Completed: 2026-08-26

## Objective

Establish a runnable, documented foundation with OIDC infrastructure, PostgreSQL,
the collaboration and core scientific registry model, initial API/UI, a safe Excel
migration preview, and automated tests.

## Affected components

- Repository documentation, ADRs, state files, and developer commands.
- FastAPI, SQLAlchemy/Alembic, auth/RBAC, sequence services, registry endpoints.
- Next.js navigation, dashboard, registry lists, and design foundation.
- PostgreSQL, Keycloak, Redis, MinIO, Caddy, Compose, and CI.
- Excel audit/import-preview scripts and migration evidence.

## Data migrations

Create the initial schema for users, teams, projects, organisms, genomes, targets,
experiment types, oligos, assays, assay roles, and audit events. Inventory,
experiment-run, validation, attachment, and mapping tables are designed but may be
introduced in following revisions with their workflows.

## API and UI changes

Expose health/readiness, current-user, dashboard summary, and read/create core
registry endpoints. Provide the scientific workspace shell and truthful empty/demo
states sourced through an API client boundary.

## Tests

Unit tests cover normalization, GC, Tm method, reverse complement, duplicate
classification, exact/reverse/ambiguous target mapping, import normalization, and
permission policy. API smoke tests and web lint/type/build are required when their
toolchains are available. Compose configuration and migration application are
deployment checks.

## Risks

- Empty initial repository and unavailable local Node/Python dependencies.
- Keycloak proxy/path behavior differs between local and institutional deployments.
- Workbook contains allocated placeholders and ambiguous source semantics.
- Docker/network access may be unavailable during the first validation run.

## Completion criteria

- Documentation and migration report match inspected evidence.
- Clean-machine Compose configuration is complete and has no production secrets.
- Core API model/migration, scientific services, importer preview, and tests exist.
- Initial web application is accessible and professionally structured.
- Available checks pass; unavailable checks and next phases are recorded in status.

## Outcome

All completion criteria were met. The core registry API, initial migration and
seed, OIDC boundary, scientific workspace, Compose/CI foundation, deterministic
Excel preview, and reproducible Primer3/BLAST worker image are implemented. The
source workbook remained read-only and no records were imported.

Validation passed through the repository `make` targets, production image builds,
an isolated PostgreSQL migration/seed check, executable version checks, and the
read-only workbook preview. Deferred domain workflows remain explicit in
`docs/project/BACKLOG.md` and were not represented as complete.
