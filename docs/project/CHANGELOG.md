# Changelog

## Unreleased

### Added

- Phase 0 source audit and persistent architecture/security/product documentation.
- Initial ADR set and completed MVP execution plan.
- FastAPI core registry, RBAC/visibility boundary, audit trail, SQLAlchemy model,
  Alembic migration, and deterministic experiment-type seed.
- Next.js scientific workspace, OIDC integration boundary, responsive registry
  pages, container stack, CI, backup/restore scaffolding, and developer commands.
- Celery bioinformatics worker with Primer3 2.6.1 Tm/hairpin/homodimer facts and
  BLAST+ 2.17.0 executables, pinned and verified for ARM64/x86_64 images.
- Optional container-backed `make` toolchain for format, lint, typecheck, and tests.
- Canonical product requirement catalogue with stable domain IDs and a living
  requirement-to-code/test/plan traceability matrix.
- Public-ID detail and authorized metadata-update APIs for oligos, targets, and
  assays, with visibility-scoped search, immutable oligo identity, audit snapshots,
  and assay version increments.
- Browser forms and workflows for core registry create, search, detail, and edit;
  contextual Forward/Reverse assay roles; expected amplicon; and global core search.
- PostgreSQL route integration tests and a Playwright Chromium journey through
  Caddy that verifies persistence after browser reload.
- Projected user profiles with provider metadata and account lifecycle, explicit
  development identities backed by PostgreSQL, signed development-session headers,
  membership-aware authorization contexts, and token refresh/logout configuration.
- Team and Project APIs and browser workflows with stable project IDs, membership
  roles, four visibility scopes, linked resources, audit events, and reload persistence.
- Personalized user/team/project dashboards, accessible identity menu and profile,
  and server-authorized administration for users, teams, projects,
  ExperimentTypes, and organisms.
- Reversible `0002_identity_workspaces` migration and deterministic local
  administrator/researcher projections with Team memberships.
- Six concern-specific Playwright specs covering smoke, authentication, Oligos,
  Targets, Assays/search, and workspaces/administration.
- ExperimentRun and contextual, append-oriented Validation APIs and browser workflows,
  including assay-version snapshots, repeated runs, supersession history, audit
  provenance, evidence-aware search, and a real awaiting-validation dashboard count.
- Private MinIO evidence uploads with SHA-256 metadata, bounded MIME/size policy,
  pending/quarantined publication state, retained soft-removal history, and reversible
  Alembic revision `0003_experiment_evidence`.
- A seventh Playwright spec covering run creation, real MinIO evidence upload,
  quarantine display, contextual validation, supersession, global search, dashboard,
  and browser-reload persistence through Caddy.
- Persistent `ScientificJob`, append-oriented attempt, and immutable Primer3 result
  records with reversible migration `0004_scientific_jobs`, idempotent API submission,
  visibility-aware reads, bounded retries, active-job limits, audit transitions, and
  PostgreSQL-authoritative results.
- Qualified Primer3 2.6.1 individual Oligo QC and Assay Forward/Reverse analysis with
  separate nearest-neighbor Tm, hairpin, homodimer, heterodimer, end-complementarity,
  and derived Tm-delta facts plus complete input/parameter/tool/build provenance.
- Oligo and Assay scientific-job browser workflows with polling, explicit role
  selection, historical/stale-version results, viewer-safe controls, and provenance.

### Changed

- Caddy now sends only `/api/v1/*` to FastAPI, preserves NextAuth `/api/auth/*`, and
  dynamically resolves recreated Compose containers.
- The standalone Next.js runtime listens on all container interfaces.
- Project reporting now distinguishes build verification, service/API runtime
  verification, and browser workflow verification.
- Core registry scope assignments now validate accessible Team/Project ownership;
  global search includes visible Projects and all development requests require an
  explicit signed session instead of an implicit administrator.
- PostgreSQL integration runs remove stale ephemeral databases before and after
  execution; browser tests share Caddy networking while using the public
  `oligospace.localhost` origin and cookie domain.
- Experiments and Validation navigation now expose working registry workflows instead
  of future-phase placeholders; unscanned evidence deliberately has no download path.
- Scientific-job submission for Assay pairs now requires visibility of both paired
  Oligos, not only the Assay.
- `make test-e2e` runs in an isolated `oligospace-e2e` Compose project with tmpfs
  storage, no host port, and public placeholders from `infra/e2e/e2e.env`; it never
  reads `.env` and is torn down after every run, so development data is untouched.
- CI gains an `integration` job running PostgreSQL integration tests with an Alembic
  downgrade/upgrade round-trip; `OLIGOSPACE_REQUIRE_INTEGRATION=1` fails on skips.
- Web unit tests report through the Node test runner.

### Validation

- Plan 005 validation on 2026-10-29: format/lint/typecheck; API 25 passed (7
  PostgreSQL tests delegated); worker 7 passed; web 2 passed; integration 7 passed with
  0 skips and Alembic round-trip; 10 Chromium tests in 8 specs including both
  scientific-job workflows in the isolated E2E stack; dev and E2E Compose configs;
  GitHub CI green on `f7fff83`. Interruption/recovery gates remain open.

- Plan 005 validation in progress on 2026-09-07: API/web/worker lint and strict typing;
  25 API unit tests; 7 worker tests including real Primer3 golden fixtures and error
  boundaries; PostgreSQL 17 upgrade/downgrade/re-upgrade through migration 0004 and
  integration tests; production API/web/worker image builds; Compose runtime health
  and host Caddy root smoke. Playwright and interruption/recovery gates remain open.

- Passed formatting, lint, strict Python/TypeScript type checks, 15 API tests,
  2 real Primer3 worker tests, web smoke test, and Next.js production build.
- Applied `0001_initial_registry` and 17 seed records to isolated PostgreSQL 17;
  removed the temporary validation stack after verification.
- Regenerated the read-only Excel preview with an unchanged source checksum.
- Passed the complete required repository checks on 2026-08-26: formatting, lint,
  strict type checks, 15 API unit tests (2 integration tests skipped there), 2
  worker tests, web tests, and production web/API image builds.
- Passed 2 PostgreSQL 17 integration tests against a fresh Alembic migration.
- Passed the Playwright core-registry journey through Caddy: root, development
  identity, dashboard, oligo create/detail/edit, target create/detail/edit, assay
  creation and versioned edit with Forward/Reverse roles, global search, and reload
  persistence.
- Passed the complete plan-003 repository matrix on 2026-09-02: format, Ruff,
  mypy, ESLint, TypeScript, 19 API unit tests, 2 real Primer3 worker tests, and web
  tests.
- Passed 3 PostgreSQL 17 integration tests after applying both Alembic revisions on
  a guaranteed-fresh database.
- Passed 6 split Chromium E2E specs through Caddy and a separate host-network smoke
  at `http://oligospace.localhost:8080`; host HTTP smoke also verified the login
  redirect, login page, and health endpoint.
- Passed the complete plan-004 matrix on 2026-09-02: formatting; Ruff, mypy,
  ESLint, and TypeScript; 21 API unit tests; 2 worker tests; web tests; Compose and
  production runtime image builds; 4 PostgreSQL tests after migrations 0001 → 0003;
  and all 7 Chromium specs through Caddy in 15.8 seconds.

### Data quality

- Documented workbook placeholders, invalid/missing sequences, orientation
  normalization, length discrepancy, and duplicate storage positions without
  changing the source file.
- Recorded both observed source checksums after the workbook changed externally
  during the audit; the latest read-only preview supersedes stale missing-value
  observations while preserving their snapshot history.
