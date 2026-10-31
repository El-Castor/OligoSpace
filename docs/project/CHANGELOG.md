# Changelog

## Unreleased

### 2026-10-31 — Isolated Scientific Soft UI prototype

- Added a development-only Next.js prototype with centralized tokens, fictional
  local interactions, state examples and no backend dependency.
- Refined paired shadows and sidebar; synthetic Brachypodium/Arabidopsis data,
  monospace sequence copy and true compact table density.
- Added Chromium interaction/accessibility checks, preserved baseline/revised
  screenshots and three design/migration documents. Production pages, scientific
  workflows and main remain unchanged; no visual migration or merge performed.

### 2026-10-31 — R1-02 lifecycle acceptance

- Added four complete Chromium lifecycle journeys for Oligos, Targets, Assays and
  Projects: deprecate/archive, reload, search and retained identity.
- Added independent PostgreSQL proofs of stable identity, exact Assay associations,
  audit transitions, invalid status/ID-change rejection, and archived Oligo duplicate
  protection. No production code change was needed.
- R1-05 merged in PR #5 (`c882e3d`, merge `537fa9c`), CI green. Plan 006 functional
  scope validated; existing R1-06/R1-07 execution prepared with confirmed D2/D9.

### 2026-10-31 — R1-05 audit evidence

- Added persisted MVP mutation/audit coverage, request correlation and concurrent
  request isolation tests. Redact structured credential/file-body fields at API
  audit insertion; retain prior history unchanged.
- Fixed dashboard recent-activity UUID disclosure after project access revocation
  using current resource visibility before event ordering/limiting.
- R1-03 integrated via PR #4 (`8a2169a`, merge `400ce69`), CI green.

### 2026-10-31 — R1-03 assay integrity

- Added the positive/negative ASSAY-004 matrix with independent-session checks
  for rejected-operation atomicity and persisted associations/version/lifecycle/audit.
- Global viewer role now prevents registry edits even for creators or contextual
  managers; identical assay metadata/association PATCH no longer invents a version.
- R1-04 integrated in PR #3 (`a352312`, merge `069323f`), CI green.

### 2026-10-31 — Plan 006 and R1-04

- Confirmed plans 001–005 are merged in main at `82e5ff4`; superseded stale
  unpushed/unmerged status without changing historical validation evidence.
- Activated Plan 006 for R1 development, starting with the four-scope registry
  visibility matrix and cross-project search/association browser regression.
- Fixed inaccessible Oligo identifiers appearing in exact-duplicate conflict
  payloads and reverse-complement suggestions. Visible matches retain reuse hints;
  institute-wide uniqueness remains enforced for hidden exact duplicates.
- Added the sole preparatory hosting plan at `docs/deployment/PILOT_HOSTING_PLAN.md`.
  No Mac mini access, installation, networking change or deployment was performed.
- Validation: format/lint/typecheck/unit checks, 91 PostgreSQL tests (0 skipped),
  11 isolated Chromium E2E tests and existing Compose validation pass locally.

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
- ADR-0006 recording PostgreSQL-authoritative scientific job state, lease-fenced
  attempts, and lease-bounded tool timeouts.

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
- Scientific-job attempts are fenced: the worker locks job and attempt rows and
  commits a result or failure only for the current running attempt; superseded
  attempts are closed as `stale_attempt` and audited as `stale_attempt_rejected`.
- The Primer3 tool timeout is bounded by the attempt lease (minus 5 s); an exhausted
  lease raises retryable `lease_exhausted` before the tool starts.
- Reconciliation locks with `SKIP LOCKED`, audits `worker_lost` and `redispatch`, and
  records the new Celery task id.

### Validation

- Plan 005 validation on 2026-10-29: format/lint/typecheck; API 25 passed (7
  PostgreSQL tests delegated); worker 7 passed; web 2 passed; integration 7 passed with
  0 skips and Alembic round-trip; 10 Chromium tests in 8 specs including both
  scientific-job workflows in the isolated E2E stack; dev and E2E Compose configs;
  GitHub CI green on `f7fff83`.
- Plan 005 interruption/recovery on 2026-10-29 (`oligospace-e2e` only): worker kill
  (A), Redis restart after completion (B1) and Redis outage at submission (B2) passed;
  stuck-job reconciliation exposed a stale attempt committing success (C0), fixed by
  attempt fencing and lease-bounded tool timeouts, then passed (C1, C2). After the
  fixes: worker 14 passed, E2E 10 passed in 14.3 s. Plan 005 completed.

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
