# Changelog

## 2026-11-01 — DEPLOY-02 qualification

PR17 merged as `75179a52da0d929922c904ff6df06d94eb7a1a67`. Added isolated
S3 compatibility/restore and OCI/native-CI qualification tooling without registry
publication or deployment. Superseding user decision excludes AIStor and makes
SeaweedFS priority 1, Garage priority 2, historical MinIO compatibility-only. Added
Garage persistent configuration and four logical restore scenarios; both platform
manifests verified. 27 static tests pass; runtime/scans/native evidence and GitHub
CI remain pending because Docker/GitHub shell access are unavailable.
See [report](../deployment/DEPLOY_02_STORAGE_RELEASE_IMAGES.md).

## 2026-11-01 — PR16 integrated; DEPLOY-01 isolated foundation

Merged approved documentation via PR16/`ab0ec42`, then added independent pilot
configuration contract, safe static diagnostics, disposable-only bounded PostgreSQL
bootstrap and migration, local tracked-source OCI/SBOM/provenance export, release
gates and CI qualification. MinIO substitution remains blocked by ADR-0007;
cached artifact tests do not establish maintenance or registry availability.
Independent review's host-volume, elevated-role, builder and stderr-evidence
findings corrected with failing-then-passing tests. Existing application unchanged;
one E2E check now verifies exact role/Oligo pairs without an unspecified SQL order.
No Mac mini, tunnel, real database, Docker volume deletion or deployment action.

## 2026-11-01 — PR #16 documentation review corrections

Retain existing Cloudflare Zero Trust/WARP as user-reported infrastructure, with
separate SSH/private-network/HTTPS/OIDC qualification and optional Tailscale only.
Separate first installation and update, qualify database readiness before one-shot
migration, and link security gates to SECURITY.md with explicit proof/decision
states. Record public MinIO metadata limits and maintenance risks, plus measured
capacity requirements for the 16 GB Mac mini and preserved co-user data.
Documentation and tracking only; no infrastructure or functional change, no merge.

## 2026-11-01 — UI-06 approved and integrated; MVP qualification proposed

User approved UI-06 visually/functionally. PR #15 exact head `535454e` merged
by merge commit `9852bdd704dc2658dd2941eeae8adb56f8ddc759` after 12 green
checks and no conflict; main synchronized without rewriting history.
Post-merge quality and 74 unit tests pass. No additional functional change.

Added a scoped, evidence-based MVP qualification dossier and extended the sole
pilot-hosting plan with immutable release inputs, proposed preparatory deliverables,
deployment/restore/rollback order and review gates. Documentation only, pending
review; no deployment scripts/configuration, installation or production service.
Existing R1-08–11 acceptance and operational prerequisites remain unexecuted.

## 2026-11-01 — UI-05 integration and UI-06 workflows

UI-05 merged via PR14 at eb7f2b2 after user approval and12 successful checks.
UI-06 shares scientific job cards with actual state/date/error/attempt history,
persisted sequence snapshots and exact clipboard copies of IDs/DNA/result JSON.
Primer3 numerical precision and units remain unchanged. Automatic refresh retains
1500ms/40-read limit and clearly reports its pause, with manual status refresh.
Source navigation and explicit service failure presentation preserve private-job
404. No backend or scientific workflow changes; UI-06 pending user review.

## 2026-11-01 — UI-04 integration and UI-05 forms

UI-04 PR13 merged by merge commit985d506 after user approval and12 green checks.
UI-05 groups scientific fields by purpose, improves label/help hierarchy and
adds shared pending/error feedback. Drafts are temporary in-memory submissions
scoped to route/identity, never browser storage; immutable/hidden credentials
and scientific context are excluded. Viewer scientific submit forms are read-only.
Existing actions, schema, units and Primer3 jobs unchanged. UI-05 pending review;
no UI-06 work.

## 2026-11-01 — UI-04 scientific tables

Shared scientific registry tables gain labeled horizontal scrolling, true compact
density, copyable IDs/DNA, full-value disclosure and aligned numeric fields.
Projects reuse the table; search shows its active query; existing API pagination
is navigable. Loading/error/denied/empty states remain distinct. Membership
removal now confirms before the unchanged server action. No backend/schema,
permissions, CSV or scientific workflow changes. Delivery pending user review;
no merge authorization for this lot.

## Unreleased

### 2026-10-31 — UI-03 cards and content surfaces

- Centralized moderate panel elevation across existing shared outer surfaces;
  retained UI-02 navigation and dense table structure.
- Removed stretched dashboard panel heights and artificial card/detail minimums;
  improved the same five statistics' hierarchy and secondary metadata readability.
- Added comparable empty/sparse/full API-backed scenarios, natural-height and
  contrast checks, retaining all business/security/scientific regression journeys.

### 2026-10-31 — UI-02 shell and navigation

- Applied prototype petroleum rail, outline brand/icons, grouped active inset
  navigation and aligned token-based headers to the production shell.
- Added mobile modal navigation, skip link, keyboard cycle, Escape/focus return
  and resize handling; improved user-menu keyboard dismissal.
- Preserved server identity/role condition, routes, team links, logout and all
  scientific content/contracts. Added role/responsive/contrast/navigation checks.

### 2026-10-31 — Scientific Soft UI production foundations

- Centralized approved semantic design tokens and applied them to existing
  production CSS primitives: palette, typography, fields, badges, raised surfaces,
  buttons, focus, alert/invalid/disabled states and reduced motion.
- Preserved component contracts and all scientific/security workflows; added
  responsive/keyboard/contrast/error E2E evidence on the real application routes.

### 2026-10-31 — MVP batches integrated; design migration prepared

- Integrated R1-06 (#7, `da58b47`) and R1-07 (#8, `7278fed`) by merge commit after
  green CI; preserved the official Soft UI reference remotely without merging it.
- Documented independent shared-component PR boundaries, invariant scientific
  contracts, regression gates and rollback. No graphical implementation change.

### 2026-10-31 — R1-07 scientific CSV

- Added authenticated filtered oligo CSV and browser download using the current
  session and visibility policy. Stored metric provenance accompanies values.
- UTF-8 BOM, quoting, formula neutralization, explicit limits and row-count/schema
  headers; empty results retain headers, oversized exports fail without truncation.
- Audit records generation, actor/correlation and safe count/filter facts without
  CSV data. Added parsed-content, permission/revocation, persistence and download tests.

### 2026-10-31 — R1-06 pilot uploads

- Default-disabled upload setting; production cannot opt in. Authenticated
  effective policy drives the server-rendered UI, which fails closed.
- Refused uploads read no file body in the handler and create no object,
  Attachment or success audit. Existing evidence remains quarantined and intact.
- Added denial/retention regressions and kept explicit dev/test quarantine tests.

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
