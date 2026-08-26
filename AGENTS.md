# OligoSpace agent guide

OligoSpace is a collaborative, traceable registry for oligonucleotides, assays,
experiments, validation, and physical inventory. Scientific records and computed
results must always retain provenance.

## Start here

Before substantial work, read this file, the nearest scoped `AGENTS.md`,
`docs/project/STATUS.md`, `ARCHITECTURE.md`, relevant ADRs, and Git status. The
source-of-truth specifications are `docs/PRODUCT_SPEC.md`, `docs/DATA_MODEL.md`,
`docs/SECURITY.md`, and the active execution plans.

## Repository map

- `apps/api`: FastAPI application and relational model.
- `apps/web`: Next.js application and scientific UI.
- `services/bioinfo-worker`: reproducible asynchronous analyses.
- `scripts/migration_excel`: read-only Excel audit and import preview tooling.
- `database`: seed/reference data; schema changes live in API Alembic revisions.
- `infra`: containers, identity, proxy, and backup operations.
- `docs`: decisions, runbooks, migration evidence, and current project state.

## Required workflow

Use `make format`, `make lint`, `make typecheck`, and `make test` before handoff;
use `make compose-config` when infrastructure changes. Never edit the source Excel
workbook or commit secrets. Database changes require an Alembic revision. API
authorization is server-side; UI visibility is not a security boundary. Computed
scientific values require algorithm, parameters, reference, and timestamp where
applicable. Never manufacture mapping, specificity, or validation results.

Update `STATUS.md`, `BACKLOG.md`, and `CHANGELOG.md` after meaningful work. Create
an ADR when an architectural decision changes and move completed execution plans
to `docs/exec-plans/completed/` with their outcome.
