# Backlog

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
