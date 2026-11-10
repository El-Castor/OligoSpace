# Backlog

## DEPLOY-04 — verified recovery delivered for code review (2026-11-10)

PR21 is merged as `ff3f629`; this supersedes its historical pending wording below.
The owner authorized this separate DEPLOY-04 lot. Single
[PR #22](https://github.com/El-Castor/OligoSpace/pull/22), isolated branch
`codex/deploy-04-backup-disaster-recovery`, from latest main after that merge.

Qualified code `953f5fb`: coordinated encrypted app/Keycloak/S3 capture with
verified writer pause/resume, preserved ownership/grants/audits/jobs/provenance,
empty-target-only restore, attachment integrity, interrupted-target fencing,
external-filesystem transfer and controlled retention. Native AMD64/ARM64 full
restores, fresh OIDC/reader permissions/new Primer3 job,11 negatives per platform
and secret logs pass.30 backup tests and107/26/23 existing controller tests pass;
mandatory make checks,206 PostgreSQL/migrations,29 Chromium per native architecture,
real OIDC/scientific and general CI/foundation pass. Review found no remaining
important code finding. [Report and proof](../deployment/DEPLOY_04_BACKUP_RECOVERY.md).

Garage's access-ID logging on unsupported GetObjectTagging remains OPEN; positive
S3 proof uses a previously qualified SeaweedFS4.52 **disposable test service only**.
No provider adoption. All DEPLOY-02/03 security/supplier/license/provenance gates
remain release-blocking, without waiver. R1-08 still needs approved off-host/vault,
capacity/retention/RPO/RTO; R1-09 and R1-10/R1-11 remain open. No Mac mini, real data,
Cloudflare, volume deletion, real migration, image publication or merge. Stop for
owner review; no DEPLOY-05. Personal working-tree files were preserved.

## DEPLOY-03 — qualified for code review (2026-11-10)

Single [PR #21](https://github.com/El-Castor/OligoSpace/pull/21), branch
`codex/deploy-03-container-hardening`, from verified main `9ebbf2c`; unmerged.
Three initial strategies and a fourth Ubuntu LTS variant were measured natively
on AMD64/ARM64. Selected digest-pinned Ubuntu/Python runtime uses a signed dated
snapshot, hashed dependencies, separate tooling and no runtime pip/compilers.
Kombu 5.6.2 and Primer3 parameters/nine references are unchanged. Targeted JWT,
multipart and Biopython security fixes are qualified; the Biopython HIGH missed
by Trivy is explicitly corrected rather than ignored.

Code `7b9dca4` passes mandatory make checks,99 API / 14 worker units,206 PostgreSQL,
29 Chromium, 16 OIDC and 7 scientific cases per native architecture. Runtime controls,
readiness, secret logs, clean stop/cleanup and eight S3 contracts pass. Final same-DB
scans:0 detected CRITICAL/HIGH, 22 MEDIUM / 4 LOW, 0 secrets per image. Four upstream IDs
with higher CVSS scores remain open; vendor priority is not a severity waiver.
All-severity release gates and DEPLOY-02 supplier/license/provenance findings
remain blocking. Independent review findings resolved; no remaining important
code finding. API OCI archives shrink 52–60%, worker 22–26%.
[Full report, retained evidence and limits](../deployment/DEPLOY_03_CONTAINER_HARDENING.md).

Chromium reuses the existing uploads-disabled no-object-service recipe because
historical MinIO is unavailable; no provider substitution. No image publication,
Mac mini deployment, Cloudflare, real migration, S3 adoption or DEPLOY-04.
R1-08/09 operations and R1-10/11 human/curated-data acceptance remain open.
Next: owner PR review. This supersedes the earlier stop-after-MVP-02 work boundary
only for the completed DEPLOY-03 lot; it grants no operational authority.

## MVP-02 — code integration only (2026-11-09)

The owner explicitly authorized PR #20 at unchanged head `3f2c83a1b8c6d449e1f6d249dfef3c462cdc5c2c`.
Merged with `--merge --match-head-commit`, without `--admin`, as
`a2f9a211fba9f5c12afadb8435d03e83b067a00b` (2026-11-08 22:59:17 UTC). Local `main` was fast-forwarded;
merge parents and exact tree equality with the approved head were verified.
Before merge: no active branch protection, ruleset or required check; functional
CI, 7 scientific OIDC, 16 OIDC, 29 Chromium and 206 PostgreSQL cases successful.
All nine DEPLOY-02 failed checks remain failed, unchanged and release-blocking.
No webhook, GitHub Pages or environment is configured; push workflows perform
CI and disposable foundation checks only, without publishing or deploying.

Post-merge [CI](https://github.com/El-Castor/OligoSpace/actions/runs/42532912311)
and [foundation](https://github.com/El-Castor/OligoSpace/actions/runs/42532912335):
**SUCCESS** on the merge commit (six application jobs and the foundation check). This four-file documentation follow-up is isolated
in a separate commit; application, workflow and retained evidence files are unchanged.
This records integration only; coverage limits, human R1-10/R1-11 acceptance,
R1-08/R1-09 operations and every DEPLOY-02 gate remain open. No Mac mini,
Cloudflare, image publication, SeaweedFS adoption or real migration is authorized
or performed. Stop after this integration report; no next work lot.

This entry supersedes earlier pending-merge wording below, preserving its history.


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

## MVP-01 follow-ups (awaiting owner prioritization)

- AUTH-B1: resolved (row-lock serialization plus PostgreSQL concurrency test).
- AUTH-B2: retire the legacy literal `keycloak` provider after pilot bootstrap.
- AUTH-B3: audit email/display-name refreshes from validated claims.
- AUTH-B4: concurrent logout/refresh/multi-tab tests, and cross-organization checks
  for audit, attachments and jobs in real OIDC (the basic journey is done).
- AUTH-B6 (priority, before pilot qualification): bounded JWKS cache with secure key
  rotation (currently one fetch per API request, which is also the actual denial path
  during a Keycloak outage); no revocation cache is to be introduced.
- DEP-1 (reproducibility risk): pin remaining transitive Celery dependencies (kombu is
  pinned at 5.6.2).
- AUTH-B5: product decision on invitation, Keycloak account creation, password-reset
  mail delivery and MFA recovery (currently absent/unqualified).

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

## DEPLOY-01 — review foundation, retain unqualified gates

User authorized PR16 merge (`ab0ec42`) and DEPLOY-01 implementation only, not merge
or real deployment. Review independent Compose, static policy/doctor, guarded
disposable bootstrap, OCI build/manifest contract and qualification tests.
Storage decision ADR-0007 remains proposed/blocked: no implicit supplier/format
change. Authorized registry, native cross-platform release evidence, production
identity/TLS/MFA/RLS/security review, complete restore and real-target installer
remain open. Preserve R1-08/09/10/11 and user-data protections. See
`../deployment/DEPLOY_01_IMPLEMENTATION.md` for actual results and acceptance limits.

## PR #16 — four documentation corrections, no implementation

Review the corrected Cloudflare/SSH/HTTPS/OIDC boundaries, bootstrap/update order,
SECURITY gate decisions (including RLS with no accepted deferral), and MinIO image
availability/maintenance/ARM64/S3 restoration. Measure future capacity on the
16 GB Mac mini (historical ~66 GiB free) before assuming simultaneous stacks;
preserve other users' data. No operational qualification is claimed. PR #16 stays
DRAFT/non-merged; no next functional or hosting lot is started.

## Current next action — qualification dossier review

2026-11-01: UI-06 was explicitly approved and PR #15 merged at `9852bdd`,
unchanged head `535454e`, after 12 successful checks. UI-02–06 are complete;
the earlier review holds below are retained as historical snapshots.
No further functional modification is started or authorized by this handoff.

Review `MVP_QUALIFICATION_AUDIT.md` and the reproducible release/deployment
sequence in `../deployment/PILOT_HOSTING_PLAN.md` §8 before implementation.
The dossier proposes targeted traceability reconciliation (notably the delivered
CSV subset), acceptance evidence, owners and go/no-go gates for existing
R1-08 backup/restore, R1-09 TLS/OIDC, R1-10 curated data and R1-11 human acceptance.
These lots remain open. Mac mini unavailability does not invalidate development
proofs, and no remote operation or infrastructure implementation is authorized.

## UI-06 — scientific workflow review

UI-05 is integrated via PR14/main eb7f2b2. UI-06 completes the approved shared
scientific interface lot only: actual job states, values/units, sequences,
provenance, error/history and bounded manual/automatic read refresh.
No new retry/cancel/design/mapping operation or fabricated progress.
User approval of captures/report required before merge. Real-device/reader
qualification, institutional OIDC and outstanding pilot operations remain distinct.

## UI-05 — implementation awaiting review

UI-04 is integrated through PR13/main985d506. UI-05 modernizes existing
scientific create/edit and supporting settings forms with shared primitives.
Validate exact payloads/units, redirect errors/drafts, pending/read-only states,
roles, lifecycle and Primer3 regressions. No new scientific field or backend
capability. Supersession error redirects retain their existing limitation; reopen
from the original evidence, never reconstruct hidden context. User capture/report
approval required before UI-05 merge. UI-06 remains deferred.

## UI-04 — awaiting visual/functional review

Implement scientific tables/list presentation on the dedicated UI-04 branch.
Preserve search/CSV/permissions, expose existing API pagination, validate density,
copy, long/missing values and real-role journeys. No configurable sort or new
business filters without API support. User review of report/captures is required
before merge; UI-05/06 remain unstarted.

## Now

- UI-03 implements real shared surfaces after validated UI-02. Dashboard panels
  now size independently to content, metadata is clearer, and no metrics or
  information are added/removed. Evidence and rollback: `docs/design/UI_03_SURFACES.md`.
  23 Chromium/198 PostgreSQL cases pass; use green-CI PR integration and report
  before starting any later graphical lot.

- UI-02 implements the real shell/sidebar/header/menu migration after approved
  PR #10. Five-width, keyboard, role and functional regression evidence is tracked
  in `docs/design/UI_02_SHELL_NAVIGATION.md` and its delivery PR. Integrate only
  with green CI; stop before the next graphical lot for the user's validation.

- Scientific Soft UI lot 1: real production tokens/primitives implemented on
  `codex/soft-ui-tokens-primitives`, with before/after route captures and regression
  gates. Await green-CI merge; report `docs/design/SOFT_UI_TOKENS_PRIMITIVES.md`.
  Do not start the next shell/navigation lot before the user's review.

- R1-06 and R1-07 are integrated via #7/#8 (`da58b47`/`7278fed`), each after
  12 green CI checks. Completed policy/CSV contracts are documented in
  `R1_06_UPLOAD_POLICY.md` and `R1_07_CSV_EXPORT.md`; 198 PostgreSQL and16 Chromium
  tests pass, along with52/14/2 units and quality gates.
- Official Soft UI reference remains on its remote prototype branch at `1aeec1a`,
  without merge. Shared-component migration is prepared in
  `docs/design/SOFT_UI_INTEGRATION_PREPARATION.md`; no global redesign is active.
  Next visual candidate is only scoped tokens/primitives in a reversible PR.
- Pilot work still open: R1-08/09 host-dependent operational qualification,
  R1-10 owner-curated data and R1-11 human acceptance. No host access authorized.

The completed R1-06/R1-07 preparation and earlier dated progress below are retained
as historical context; this entry supersedes their pending status.

- R1-06 merged via #7 (`bb91c20` / `da58b47`),12 green CI checks. R1-07 oligo
  export implemented and under final delivery checks; contract and limitations in
  `R1_07_CSV_EXPORT.md`. Next after green-CI merge: shared-component design
  migration preparation, plus existing R1-08/09/10/11 prerequisites and acceptance.

- R1-06 implementation complete: fail-closed pilot uploads, retained quarantine,
  policy-driven UI; tests 39/14/2 units,195 PostgreSQL,15 Chromium. PR/green CI
  integration pending. Next: R1-07 minimal scientific CSV. Prototype `1aeec1a`
  is backed up remotely and approved as official visual reference, not merged.

- Plan 006 functional batches are implemented and locally validated; R1-04/#3,
  R1-03/#4 and R1-05/#5 are merged with green CI. R1-02 is the final delivery
  branch, with 193 PostgreSQL / 15 Chromium cases. See GitHub for its integration.
- Next execution: R1-06 then R1-07, using the confirmed D2/D9 decisions and the
  preparation below. No host prerequisite; Mac mini deployment remains deferred.

The older progress entries below are retained as dated checkpoints and superseded
by the state above.

- R1-03 integrated via PR #4 (`8a2169a`, merge `400ce69`), all 12 CI checks green.
  Current batch R1-05; next R1-02, then confirmed R1-06/R1-07.

- R1-04 is merged in PR #3 (`a352312`, merge `069323f`), with 12 green CI checks.
  R1-03 is the current batch; after its integration continue R1-05, then R1-02.
  This supersedes the earlier uncommitted R1-04 note below.
- D2 and D9 are confirmed: execute R1-06 (disable pilot uploads), then R1-07
  (minimal visibility-filtered CSV with audit) after the current Plan 006 batches.

- 2026-10-31: Plan 006 activated by the user's continuation request. R1-04 visibility
  enforcement (AUTH-004/SEARCH-003) is validated locally (111 PostgreSQL cases and
  11 E2E tests); changes are uncommitted on `codex/plan-006-r1-visibility`.
  Next functional batch: R1-03 Assay negative
  authorization matrix (ASSAY-004), R1-05 audit coverage without data leakage
  (AUDIT-001/002), and R1-02 lifecycle E2E. See the active execution plan.
- R1 functional batches must proceed independently of the unavailable Mac mini.
  Hosting preparation is confined to `docs/deployment/PILOT_HOSTING_PLAN.md`;
  deployment, remote audit, networking and installation remain unexecuted.
- Review the deterministic Excel preview, target decomposition, and storage
  conflicts with a data owner; require explicit approval before import writes.

## Next

- Exact target-mapping persistence and interactive GeneOligoViewer.
- Inventory, orders, hierarchical locations, events, and QR workflows.
- Integrate malware scanning before any evidence attachment publication or download.

## Later

- Reference ingestion, transcript structures, and BLAST specificity.
- PostgreSQL RLS, production observability, rate limits, upload malware scanning.
- Institutional OIDC browser qualification including refresh, logout, and account
  disablement with production-like Keycloak policy.
- pgBackRest/WAL deployment and verified INRAE pull replication.

## Ideas

- Saved searches/views, favorites, reuse analytics, barcode label templates.
- JBrowse 2 integration once governed genome references exist.

## Technical debt

- Introduce a separate least-privilege PostgreSQL worker role before production.
- Scientific jobs: add lease heartbeat/renewal, rotate the claim token per attempt, and
  use a fresh Celery task id per retry (Plan 005 residual risks).
- Hide unavailable Oligo edit controls for read-only users; server-side denial is
  retained and covered in the cross-project browser scenario.
- Write a local-execution runbook for scientific jobs and the E2E stack.
- Generate TypeScript API types from OpenAPI after endpoint stabilization.
- Migrate to ESLint 10 when the Next.js lint plugin dependency graph supports it.
- Add isolated seeded fixtures per Playwright spec if parallel browser execution is
  enabled; the current specs run serially against one shared, ephemeral E2E stack.

## Completed / superseded status (2026-10-31)

- Plans 001–005 are integrated into main at `82e5ff4` (local and remote-tracking
  refs observed). The old push/merge gates are satisfied in Git; no new merge is
  needed. Live remote CI status was not re-audited.
- Worker test monkeypatch typing was fixed in `4058eb8`, already included in main.
- Plan 005 recovery scenarios cover R1-01. No new host is needed to continue R1-04,
  R1-03, R1-05 or R1-02. R1-08/09 host execution and R1-11 human pilot acceptance
  retain their specific future prerequisites.

## Execution preparation — existing R1-06 and R1-07 batches

D2/D9 were explicitly confirmed by the user on 2026-10-31. This is execution
preparation for the existing lots, not a new roadmap. Execute each on its own
branch, with demonstrated-defect fixes, tests, quality checks, commit/PR and green
CI merge commit; no force push, squash/rebase or protection bypass.

### R1-06 — uploads disabled for the pilot

- Add an explicit server-enforced pilot upload policy, disabled by default in
  the pilot configuration. Preserve development/test upload coverage through an
  explicit setting; production must fail closed. Do not change existing networks
  or create a production service to verify this policy.
- Refuse disabled uploads with a stable 403/501 problem and clear message before
  storing file bytes/objects or creating an Attachment. Hide the form or explain
  its unavailability; UI visibility is not the permission boundary.
- Retain existing quarantined records and their audit history, without enabling
  publication/download. Regression: disabled upload has no DB/object mutation or
  success audit; enabled dev/test path remains quarantined and audited; Chromium
  verifies the pilot explanation. Run existing evidence and permission tests.

### R1-07 — mandatory minimal CSV export

- Export visible search results server-side, reusing the current list/search
  policies and filters. Define the small implemented entity set and column contract
  explicitly in this batch before coding; preserve stable public IDs, status and
  type, with no sensitive/internal fields or invented scientific results.
- Handle CSV quoting, Unicode, empty results and spreadsheet formula injection;
  enforce a documented size/pagination bound and a truthful row count. Browser
  download uses the authenticated session and appropriate CSV content headers.
- Audit the successful export with actor, timestamp, request correlation, safe
  filter facts and row count; do not copy the CSV body or raw credentials into audit.
- Reuse R1-04 audiences/scopes for non-leakage and compare parsed CSV rows with the
  visible API query; verify PostgreSQL audit persistence and the Chromium download.
  Run full relevant gates before PR integration. This lot has no dependency on the
  Mac mini, institutional OIDC, backup endpoints or a production deployment.
