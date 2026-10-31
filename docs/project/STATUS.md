# Project status

Last updated: 2026-10-31

## Current phase

### UI-03 — cards, panels and surfaces

UI-02 integration was confirmed remotely: PR #11, merge `5598ebd`, 12 green
checks. UI-03 on `codex/ui-03-surfaces-panels` changes only production surface
CSS/tokens: stronger balanced elevation, natural panel/card/detail heights,
clearer statistics and metadata. No backend, React contracts, scientific data
or UI-02 navigation change. Comparable empty/sparse/full real-route evidence:
`docs/design/UI_03_SURFACES.md`. 23 Chromium and198 PostgreSQL cases pass;
integration follows the exact-head green-CI merge gate. No UI-04/05/06 started.

### UI-02 — production shell and navigation

Following the user's validation of PR #10, UI-02 migrates AppShell presentation,
petroleum sidebar, grouped active navigation, headers and user menu. Mobile
navigation is now available through a native modal with explicit keyboard cycle,
Escape/focus return and resize closure. Existing `/me`, role menus, links,
logout, server actions and scientific children remain unchanged. Delivery branch:
`codex/ui-02-shell-navigation`; evidence and limits:
`docs/design/UI_02_SHELL_NAVIGATION.md`. Integration uses a green-CI merge commit.
No subsequent graphical lot is started; next work awaits this lot's validation.

### Scientific Soft UI — first production lot

User authorized production token/primitives integration from `d563165`, using
prototype `1aeec1a` as reference. Branch `codex/soft-ui-tokens-primitives` adopts
the semantic palette, typography, spacing/elevation/radius tokens and existing
button/field/badge/focus/error/disabled classes. Only production CSS changes;
no React/server-action/API/permission/schema contract change. Before/after real
route captures and tests are described in `docs/design/SOFT_UI_TOKENS_PRIMITIVES.md`.
Local verification: 18 Chromium, 198 PostgreSQL and 52/14/2 unit tests pass;
format/lint/typecheck and production builds pass. PR/CI integration is the gate.
Next shell/navigation lot requires this report's
review before proceeding; no global migration is active.

### MVP functional delivery and official design reference

- R1-06: `bb91c20`, PR #7, merge `da58b47`; 12 push/PR CI checks succeeded.
  Uploads fail closed in the pilot; existing evidence is retained.
- R1-07: `ecce1a9`, PR #8, merge `7278fed`; 12 push/PR CI checks succeeded.
  Authenticated visible/search-filtered oligo CSV includes stored provenance,
  formula protection, safe correlated audit and explicit bounds.
- Final functional verification: format/lint/typecheck pass; 52 API / 14 worker /
  2 web unit tests; 198 real PostgreSQL cases with migration round-trip; 16 Chromium
  E2E journeys. Isolated test containers were removed; no development data target.
- Official design reference: remote branch `codex/scientific-soft-ui-prototype`,
  `1aeec1a2135d006d700286a506242d2a51142c99`, user-approved iteration 02.
  No secrets/real scientific data/temporary artifacts were found in its scoped
  source, fixtures and captured UI review. Prototype push CI succeeded; no PR/merge.
  Its sole local container was stopped without affecting other services.
- Progressive graphical integration is prepared in
  `docs/design/SOFT_UI_INTEGRATION_PREPARATION.md`. No visual production component
  has been migrated. Next candidate: scoped tokens/shared primitives, separate PR.
- Remaining pilot acceptance: R1-08 backup/restore, R1-09 TLS/session qualification
  when hosting is available; R1-10 curated data approved by its owner; R1-11 human
  scientific acceptance. Mac mini remains unavailable and uncontacted.

This ledger supersedes earlier pre-integration snapshots below.

### R1-06 integrated; R1-07 delivery

R1-06: commit `bb91c20`, PR #7, merge `da58b47`, all 12 push/PR CI checks green.
R1-07 implements oligo CSV using existing search/visibility, stored provenance,
UTF-8 BOM, formula neutralization, bounded generation and correlated safe audit.
Validation: 52 API / 14 worker / 2 web unit tests; 198 PostgreSQL cases including
CSV in the R1-04 matrix; 16 Chromium E2E. Format/lint/typecheck and runtime builds
pass. PR/CI integration remains the gate; no scientific data or schema change.

### R1-06 — pilot upload policy

Prototype reference `1aeec1a` is preserved remotely on
`codex/scientific-soft-ui-prototype`, without merge; its container is stopped.
R1-06 disables uploads by default and unconditionally in production, with an
authenticated policy-driven UI and retained existing evidence. Local validation:
39 API / 14 worker / 2 web units, 195 PostgreSQL, 15 Chromium; format/lint/typecheck
and Compose configuration pass. PR/CI integration is the next gate, then R1-07.

### Plan 006 delivery ledger (latest state)

- R1-05 integrated via PR #5: commit `c882e3d`, merge `537fa9c`; push and PR CI
  succeeded. Local evidence: 189 PostgreSQL / 11 Chromium / 35 API / 14 worker /
  2 web unit tests; format/lint/typecheck passed.
- R1-02: four full Chromium lifecycle journeys added, plus PostgreSQL stable-ID,
  exact Assay association, version and audit checks. All 15 Chromium tests pass;
  PostgreSQL suite has 193 cases. No production code defect found or changed.
  Delivery branch `codex/plan-006-r1-lifecycle` follows the same green-CI merge gate.
- Plan 006 functional implementation and execution validation are complete; its
  outcome is in `docs/exec-plans/completed/006-r1-pilot-readiness.md`. GitHub PRs
  and the session checkpoint record integration SHAs. Next: R1-06, then R1-07;
  execution preparation is in BACKLOG, using the existing lot decomposition.

### Earlier checkpoints (superseded by the delivery ledger above)

- R1-03 integrated via PR #4: commit `8a2169a`, merge `400ce69`; all 12 CI checks
  passed. R1-05 is now the active branch `codex/plan-006-r1-audit`.
- R1-05 adds the mutation/audit matrix, validated request correlation, recursive
  structured-fact redaction and visibility-filtered recent activity after revocation.
  Regressions were reproduced before fixes. Coverage and limitations:
  `R1_05_AUDIT_COVERAGE.md`. Validated locally: 189 PostgreSQL tests, 35 API /
  14 worker / 2 web unit tests, 11 isolated Chromium tests, format/lint/typecheck.
  Review credential-alias finding reproduced (3 failed tests), fixed and verified.
  PR/CI integration remains next; no history or schema rewrite.

- R1-04: integrated via PR #3, commit `a352312`, merge `069323f`; 12 CI checks
  passed on the exact head. Local evidence: 111 PostgreSQL, 11 Chromium, 25 API /
  14 worker / 2 web unit tests, format/lint/typecheck. No protection/ruleset on
  main was reported by GitHub; no rule or bypass setting was changed.
- R1-03: backend matrix and fixes under validation on
  `codex/plan-006-r1-assay-integrity`. See `R1_03_ASSAY_MATRIX.md`. Viewer ownership /
  contextual-manager edit bypass and artificial no-op versions were reproduced
  before their fixes. PostgreSQL validation: 150 passed; Chromium: 11 passed;
  API/worker/web units: 26/14/2; format/lint/typecheck passed. Scoped review found
  no blocking issue. PR/merge remains to be performed after CI.
- D2/D9 confirmed by the user: R1-06 pilot uploads disabled, then mandatory R1-07
  minimal CSV. Execute after R1-05/R1-02. Mac mini deployment remains deferred.

This dated ledger supersedes the earlier pre-commit R1-04 state below.

Execution plans 001 through 005 are complete and integrated into `main`:
local `main` and `origin/main` both pointed to merge commit `82e5ff4` when this
session started (PR #2; recovery fixes and ADR-0006 included). This supersedes the
2026-10-29 unpushed/unmerged report; live GitHub CI has not been queried here.
Plan 006 was activated at `docs/exec-plans/completed/006-r1-pilot-readiness.md`, following
the user's 2026-10-31 authorization. R1-04 is the first batch, then R1-03,
R1-05 and R1-02. R1-01 is covered by completed Plan 005 recovery evidence.

The Mac mini is unavailable. No connection, audit, installation, network change,
or deployment on that machine is authorized. Functional development proceeds
independently. The sole preparatory hosting deliverable is
`docs/deployment/PILOT_HOSTING_PLAN.md`: isolated dev/pilot Compose environments,
private access, OIDC/TLS, versioned multiarchitecture images, secrets, backups and
future Linux migration. Its deployment checklist is unexecuted.

Plan 004 added experiment runs,
contextual validation, and quarantined evidence attachments. Plan 005, Persistent
scientific jobs and Primer3 analysis, completed on 2026-10-29 with individual Oligo QC
and Forward/Reverse Assay pair analysis, including validated worker/Redis interruption
and reconciliation recovery. The development application is a usable multi-user
registry through Caddy.
No production deployment exists.

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
  head), and passes 193 integration tests with zero skips enforced by
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

- `make test-e2e` passes 15 Chromium tests in 10 spec files through Caddy: smoke and
  personalized dashboard; development login/profile/logout/second identity;
  Oligo; Target; Assay plus global search; Project/Team/Admin workflows; evidence;
  scientific jobs, cross-project visibility and four lifecycle journeys. It runs
  in the isolated `oligospace-e2e` Compose project
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

- Plan 005 is complete (2026-10-29). Interruption/recovery scenarios A (worker
  kill), B1/B2 (Redis restart and Redis outage at submission), and C (stuck-job
  reconciliation) passed on the isolated `oligospace-e2e` stack. Scenario C first
  exposed a stale attempt committing success (C0); attempt fencing and a
  lease-bounded tool timeout fixed it and C1/C2 were retested. Evidence:
  `docs/project/PLAN_005_RECOVERY_EVIDENCE.md`. Residual risks (no lease heartbeat,
  claim token not rotated, Celery task id reused on retry) are tracked in the backlog.
- Plan 006: R1-04 implementation is integrated via PR #3.
  It adds a four-scope, four-role PostgreSQL matrix for Oligos,
  Targets and Assays, database-projected memberships, search and list totals,
  association choices, detail and dashboard counts, and membership revocation.
  Two identifier leaks were reproduced in exact-duplicate conflicts and
  reverse-complement suggestions and corrected using the existing visibility policy.
  Exact sequence uniqueness remains institute-wide; a generic 409 still reveals
  a registration conflict but no inaccessible record identifier or metadata.
- R1-03 negative Assay matrix, R1-05 mutation/audit coverage and R1-02 lifecycle
  browser acceptance are implemented and validated; see the delivery ledger.
  R1-06/R1-07 are next and do not depend on the Mac mini.
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
- Read-only users can currently see the Oligo edit link/form; the API rejects edits.
  Hiding unavailable controls is UI follow-up, not the authorization boundary.
- ESLint 9 remains pinned until the Next.js plugin dependency graph accepts ESLint 10.

## R1-04 validation snapshot (2026-10-31)

- `make format lint typecheck test PYTHON_RUNNER=container` — exit 0. API:
  25 passed, 111 integration cases skipped in the unit-only invocation; worker:
  14 passed; web: 2 passed. PostgreSQL cases executed separately below.
- `make test-integration` — exit 0: 111 passed, 0 failed, 0 skipped; fresh PostgreSQL
  17 database, migrations 0001–0004 and downgrade/upgrade round-trip; test container
  removed afterward. The 104 new cases comprise 72 registry matrix cases and 32
  exact/reverse suggestion checks across four scopes and owner/member/unrelated/foreign identities.
- `make test-e2e` — exit 0: 11 Chromium tests, 0 failed, 0 skipped, in 9 specs
  through Caddy on the isolated `oligospace-e2e` stack, then teardown. The new test
  checks two projects, private/institute records, search counts, reload, assay
  choices, inaccessible detail and server-denied edits with unchanged data.
- `make compose-config` — exit 0 for existing dev/E2E definitions. No deployment
  configuration was changed. API/web/worker runtime builds passed as part of E2E.
- Regression evidence before the fix: 2 failures disclosed hidden Oligo public IDs
  in exact-duplicate and reverse-complement responses; the existing 7 cases passed.
- Scoped independent code review found no Critical/Important issues. Team revocation,
  post-revocation dashboard counts and nonzero pagination offset were added after
  review. Direct suggestion checks for member identities and foreign organizations now
  also verify persisted effects and institute-scoped uniqueness.
- No new live GitHub CI result, OIDC pilot qualification, Mac mini inspection,
  backup execution or Linux migration is claimed. Development data was not used
  as a test target; no before/after row-count comparison was repeated this session.

## Previous validation evidence (2026-10-29)

All on 2026-10-29 via `PYTHON_RUNNER=container` unless noted:

- `make format lint typecheck` — passed (Ruff, mypy, ESLint, TypeScript).
- `make test` — passed: API 25 passed, 7 skipped (PostgreSQL tests delegated to
  `make test-integration`); bioinfo worker 14 passed (including 7 attempt-fencing
  tests); web 2 passed, 0 skipped.
- `make test-integration` — passed: 7 passed, 0 skipped; Alembic round-trip OK;
  fresh test container removed after execution.
- `make test-e2e` — passed: 10 passed, 0 failed, 0 skipped in 14.3 s in the
  isolated `oligospace-e2e` project. Dev database row counts, containers, volumes,
  and images were identical before and after the run.
- `make compose-config` — passed for the dev and E2E configurations.
- Interruption/recovery scenarios A, B1, B2, C1, C2 on `oligospace-e2e` — passed;
  six jobs ended `succeeded` with exactly one result each (C0 defect fixed).
- GitHub CI on `f7fff83` — backend, frontend, bioinfo-worker, migration,
  integration, and compose jobs succeeded. `529fc2d` and later local commits have no
  CI run (not pushed).
- Host-network Chromium smoke (2026-09-07) — passed: 1 smoke spec at
  `http://oligospace.localhost:8080`.
- Host HTTP smoke (2026-09-07) — root `307` to login, login `200`, health
  `200`/`status: ok`.

Database migration: `0004_scientific_jobs` is applied to the development PostgreSQL
database (observed) and to a fresh isolated PostgreSQL 17 database, including the
downgrade/upgrade round-trip.
