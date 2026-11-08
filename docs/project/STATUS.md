# Project status

## MVP-02 — scientific acceptance delivered for review (2026-11-08)

Single [PR #20](https://github.com/El-Castor/OligoSpace/pull/20), branch
`codex/mvp-02-scientific-acceptance`, from main `5e34340`; no merge/release.
Scientific acceptance passes 7/7 with real HTTPS Keycloak/PostgreSQL/Primer3 on
local ARM64 and CI x86_64. Nine reference facts have zero numerical difference;
six repeated requests produce one job/no 500s. Admin/editor/reader, two institutes,
revocation/demotion, persisted failed jobs, all16 CSV columns and mobile/desktop
are verified. Idempotency defect fixed; evidence cleanup and exact six-download
CSV-audit gate corrected after independent review, with no further findings.
Mandatory make checks pass: 99 API/14 worker/15 web units,206 PostgreSQL with
migration round-trip,29 Chromium; existing16OIDC and CI application jobs pass.
[Report, retained proofs and limitations](../mvp/MVP_02_SCIENTIFIC_ACCEPTANCE.md).
DEPLOY-triggered security/storage checks remain red and untouched; no all-CI-green
or pilot approval is claimed. Next: user review and R1-10/11 human scientific
acceptance; existing R1-08/09/DEPLOY gates remain separate. Personal files retained.

## MVP-01 — real OIDC authentication merged into main (2026-11-03)

PR19 merged into `main` as `dc012e8fe161ed08380947887371dafdc611f2de` (merge commit)
from the owner-approved head `4285d4f58aeb09b21a44447f1110d02bccb815ce`, using
`--match-head-commit`, no `--admin`; `main` had no branch protection or ruleset and
no required checks. Post-merge `CI` and `Deployment foundation` on `main`: success.
No workflow publishes images or deploys on push to `main`.

**Scope of the authorization: integration of code only.** It is not a pilot approval,
not a deployment approval, and not a waiver of any DEPLOY-02 scanner or finding.
DEPLOY-02 scan gates remain red on PRs and release-blocking; they were not modified.
No deployment, Cloudflare change, image publication, storage adoption or data
migration was performed.

Qualification at code SHA `dc672aa`: real-OIDC 16/16 (AUTH-B1 last-admin race fixed,
cross-organization isolation, introspection load and Keycloak outage cases,
`kombu==5.6.2` pinned). See the
[acceptance dossier](../mvp/MVP_01_AUTHENTICATION_ACCEPTANCE.md).

Priority follow-ups: **AUTH-B6** (bounded JWKS cache with secure key rotation, to be
done before pilot qualification) and **DEP-1** (pin transitive Celery dependencies,
reproducibility risk). ResearchBrain/Basic Memory not reachable from this session, so
not updated.

## MVP-01 — delivered for review (superseded, 2026-11-03)

PR19 (was DRAFT): real HTTPS Keycloak/PostgreSQL/Next.js/API/Chromium
qualification passes 16/16 at code SHA `dc672aa` (AUTH-B1 last-admin race fixed,
cross-organization journey, introspection load and Keycloak-outage cases added,
`kombu==5.6.2` pinned); unit, PostgreSQL, migration, frontend and existing Chromium
checks pass. Remaining red checks are the DEPLOY-02 vulnerability
gates only (not waived). Independent review done; findings in the
[acceptance dossier](../mvp/MVP_01_AUTHENTICATION_ACCEPTANCE.md). No pilot approval,
deployment, merge, Mac mini or Cloudflare change. Work stops for owner review.

## MVP-01 — real OIDC authentication qualification (history)

DEPLOY-02 PR18 is merged at5e10b750889275a0db76a94fdb1e85c83f95e88b,
approved head7c81574, integration only. Historical no-merge statements below are
superseded by the owner's explicit limited authorization, not by security clearance.
All residual findings and release gates remain open; reexamine2026-11-16 or sooner.
Priority security backlog: evaluate minimal/alternative Debian13 API/worker images
preserving Python/Primer3/BLAST and native ARM64/AMD64 reproducibility. Not part of
MVP-01 implementation and no image migration/pilot approval is implied.

MVP-01 retains existing Keycloak/NextAuth/API identity and admin provisioning;
qualifies revocation/logout/refresh and roles using disposable real OIDC, no
development bypass. One branch and PR; no automatic merge or real deployment.
See [acceptance dossier](../mvp/MVP_01_AUTHENTICATION_ACCEPTANCE.md).


Decision review: [one-page DEPLOY-02 synthesis](../deployment/DEPLOY_02_DECISION.md).
Single PR18 retained; no new remediation. Merge still blocked pending explicit
risk decision or resolution; release/deployment prerequisites are distinguished.
GitHub head0b12667 checked: functional CI passes, security scan gates remain red.
No waiver, merge, provider switch or deployment authorized.

## DEPLOY-02 — targeted review, integration proposal only (2026-11-02)

Reviewed `1cca325`; qualification controller `44bb074`. The44 HIGH occurrences
per API/worker image equal9 CVEs,6 Debian sources and17 installed binary packages.
All9 remain open in trixie;8 have unstable fixes, not supported stable upgrades.
Four native probes confirm actual files; no package removed or finding waived.
SeaweedFS4.52 immutable variant: go-jose4.1.6 observed on both architectures,
6/6 self/cross restores pass; scans still block on3 UNKNOWN and38 license
observations per image. Default4.51 and pilot Compose unchanged.
Garage source SBOM542 components, source scan1 HIGH/3 MEDIUM/7 LOW;
OCI binaries equal official downloads on both architectures, but authenticated
source/build binding and runtime inventory remain unverified.
Application/foundation CI and Chromium pass at44bb074; release/security gates
remain red.88 local qualification tests pass. User cancelled the unexecuted A/B split. Keep all work together in PR18.
Final recommendation: further security corrections/decisions required; do not merge. PR18 stays DRAFT/unmerged pending user review; no deployment,
release publication, provider switch or security-policy change.
[Targeted report](../deployment/DEPLOY_02_TARGETED_REVIEW.md).

## DEPLOY-02 — security remediated, residual gates blocked (2026-11-02)

PR18 remains DRAFT/unmerged. Tested code `98a3250`: all reported application
CRITICAL removed; web scans clean on ARM64/AMD64. API/worker each retain44 HIGH
system occurrences per architecture, plus lower/unknown findings; every finding
still blocks. Zero final secret alerts. Historical JWTs are public PyJWT demo
strings in pip download cache, verified in RAM without values retained; cache
is excluded from final images. Eight S3 self/cross restores pass, nine Primer3
facts match both architectures and validated reference (delta0). Six OCI artifacts
and12 sanitized SBOM/provenance projections retained. Application/foundation CI
pass;29 Chromium journeys passed in the isolated uploads-disabled recipe.
69 local qualification tests, lint/format and Compose config pass; local combined
make cannot access Docker socket, so application suites run remotely.

Separate candidate scans: SeaweedFS4.51 has1 HIGH +3 UNKNOWN and license obligations;
Garage2.5.0 has no usable OS/Rust package inventory, gate not_verified. Signatures,
provenance trust and supplier acceptance remain open. SeaweedFS stays conditional
first candidate; Garage second, historical MinIO reference, AIStor excluded.
No pilot Compose/provider, Mac mini, Cloudflare, real data or release publication
changed. Stop for review; no automatic merge or next functional lot.
[Security report/matrix](../deployment/DEPLOY_02_SECURITY_REMEDIATION.md) and
[retained evidence](../../infra/deployment/evidence/security-98a3250-remediation.json).
This current entry supersedes the historical holds below.

## DEPLOY-01 — foundation delivered for review, pilot gates still open

PR16 merged at `ab0ec42144dbc34629b2675cc67b4364d5abc820` after exact approved
`6aba60a`,12 successful checks and no conflict. main synchronized; dedicated
`codex/deploy-01-reproducible-foundation` implements independent required-digest
pilot definition, static refusals, guarded disposable bootstrap/migrations,
local OCI build/export and release evidence gates. No activated pilot or ready
installer. Report: `../deployment/DEPLOY_01_IMPLEMENTATION.md`.

Storage maintenance/registry decision remains blocked (proposed ADR-0007);
cached ARM64 MinIO compatibility and isolated PG/runtime tests do not close R1-08/09.
No scientific/frontend logic, existing Compose, real host/tunnel/network/volume,
or existing secret changed. The sole web edit is a demonstrated E2E association
ordering assumption, replaced by exact persisted (Oligo,role) checks.
DEPLOY-01 PR must remain unmerged pending review; no Mac mini contact/deployment.

## PR #16 — documentation corrections awaiting review

The user approved the general strategy and requested four documentation-only
corrections: existing Cloudflare/WARP access (historical user report, application
HTTPS/OIDC unqualified), separate initial/update procedures, SECURITY-linked gates
with no implicit deferral, and explicit MinIO provenance/availability/maintenance
plus the real 16 GB RAM / historical ~66 GiB capacity constraint. The two main
documents incorporate these corrections. No host, tunnel, Docker configuration,
object data, volume or secret change; PR #16 remains DRAFT and must not be merged.
Public registry metadata/source consultation does not qualify a MinIO runtime.

## Current handoff — UI-06 integrated; qualification preparation only

2026-11-01: user approved UI-06 visually/functionally and authorized PR #15.
Exact head `535454ef6a12de0815dec8ef21546695625fb9a8`, all 12 checks
`COMPLETED/SUCCESS`, `CLEAN/MERGEABLE`; merge commit
`9852bdd704dc2658dd2941eeae8adb56f8ddc759`. Local `main` synchronized by
fast-forward with `origin/main`. Post-merge format/lint/typecheck and 74 units
pass; the 198 PostgreSQL cases are delegated to their separate suite, last
executed with the 29 Chromium journeys for the integrated UI-06 head.
The merge-commit CI also passed: Actions run `41300133863`, six successful jobs.

UI-02 through UI-06 are integrated. The former review holds in the dated ledger
below are superseded by these approvals; no new functional work is authorized.
Documentation-only branch `codex/mvp-qualification-plan` prepares
`MVP_QUALIFICATION_AUDIT.md` and §8 of
`../deployment/PILOT_HOSTING_PLAN.md` for review. R1-08/09/10/11 remain open;
neither hosted-pilot acceptance nor a deployment is claimed. No Mac mini,
Cloudflare, network or production changes. Personal `assests/` files retained.

### UI-06 — scientific workflows

UI-05 PR14 merged at `eb7f2b2` after explicit user approval, unchanged
`fb6b661`,12 successful checks and no conflict. UI-06 branch
`codex/ui-06-scientific-workflows` harmonizes real Primer3 QC/pair jobs, stored
input/results, attempts, errors, timestamps and bounded refresh feedback.
No backend/API/worker/scheduler/schema or idempotency change. Report:
`docs/design/UI_06_SCIENTIFIC_WORKFLOWS.md`. Before/after use the same persisted
job rows and identical values. UI-06 PR must remain unmerged pending explicit
user visual/functional approval.

### UI-05 — scientific forms and editors

UI-04 PR #13 merged at `985d506` after explicit user visual/technical approval,
unchanged head `c0bb4ff`,12 successful checks and no conflict. UI-05 branch
`codex/ui-05-scientific-forms` adds shared fieldset sections, pending submits,
focused error summaries and transient same-route form drafts. Existing API,
scientific constraints, server actions and UI-02/03/04 presentation remain.
Viewer scientific submissions are suppressed using /me; resource permissions
remain enforced by the API. Report: `docs/design/UI_05_SCIENTIFIC_FORMS.md`.
UI-05 PR must remain unmerged until explicit user approval; UI-06 not started.

### UI-04 — scientific tables and lists

UI-03 was visually approved and integrated via PR #12, merge `1faf7ba`.
UI-04 branch `codex/ui-04-scientific-tables` migrates the shared registry table,
project list, existing list metadata and confirmation of membership removal.
Small client controls add real compact density, ID/DNA copy and full-value
inspection. Existing server q/limit/offset and CSV contracts stay intact;
registry failures no longer masquerade as empty results. No backend/schema or
UI-02 navigation changes. Report: `docs/design/UI_04_SCIENTIFIC_TABLES.md`.
PR must remain unmerged until user reviews captures and report; UI-05/06 deferred.

Last updated: 2026-11-01

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
