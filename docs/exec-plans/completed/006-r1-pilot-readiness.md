# Plan 006 — R1 pilot readiness

- Activated: 2026-10-31, by the user's development-continuation request.
- Base: `82e5ff4` on `main`, including merged plans 001–005 (PRs #1/#2).
- Status: functional implementation and execution validation completed 2026-10-31.
- Specifications: `docs/PRODUCT_SPEC.md`, `docs/DATA_MODEL.md`, `docs/SECURITY.md`.
- Prior decomposition: `docs/audit/2026-10-28/08_EXECUTION_BACKLOG.md` (historical proposal).

## Scope and order

Continue functional development independently of the unavailable Mac mini. Do not
contact that machine, change networks, install hosting software, deploy services,
or repeat the general audit. Work on a dedicated local branch. Do not replay
already-completed Plan 005 recovery scenarios simply to activate this plan.

1. **R1-04 — AUTH-004 / SEARCH-003:** PostgreSQL integration matrix for Oligo,
   Target and Assay across Private/Project/Team/Institute, four global roles,
   owner, team-only, project-only, both, unrelated and foreign-institute identities.
   Resolve memberships from database rows. Verify list choices, totals, pagination,
   detail, ID/name/scientific-field search and dashboard counts. Revoke membership
   and verify access disappears. Reproduce and correct any identifier disclosure
   from duplicate and reverse-complement reuse suggestions. Keep organization-wide
   sequence uniqueness; an inaccessible exact duplicate returns a generic conflict.
   Browser regression: private records absent from search and assay selectors for
   another user; visible records remain available.
2. **R1-03 — ASSAY-004:** negative API matrix for experiment-type roles, duplicate
   associations, inaccessible oligos/targets, unauthorized edits and foreign scope.
3. **R1-05 — AUDIT-001/002:** mutation-to-audit coverage and sensitive payload tests.
4. **R1-02 — lifecycle:** Chromium deprecation/archive and stable identity checks
   for projects, targets, oligos and assays, with audit evidence.

R1-01 is already covered by completed Plan 005 and its recovery evidence. Reuse
that evidence; do not manufacture a new acceptance result. R0 integration and test
isolation are present in main. R0 documentation alignment is part of this session;
stash deletion is outside scope. Live remote CI status must be verified separately
before any future merge; a local remote-tracking ref is not CI evidence.

## Hosting boundary and later batches

The sole hosting deliverable is `docs/deployment/PILOT_HOSTING_PLAN.md`, a proposal
derived from the repository. R1-08/09 execution waits for an available authorized
host and OIDC/TLS inputs; this does not block the four functional batches above.
On 2026-10-31 the user confirmed D2 and D9: R1-06 disables uploads for the pilot,
and R1-07 must provide a minimal visibility-filtered CSV export. Execute these
after the four functional batches above; retain their existing backlog scope.
R1-10 still requires curated data. R1-11 remains human scientific acceptance.

## Validation and completion

For each batch, add regression tests before fixes and record actual outcomes.
Run `make format`, `make lint`, `make typecheck`, `make test`, PostgreSQL
`make test-integration` and isolated `make test-e2e`. Run `make compose-config`
if infrastructure changes. Preserve the existing dev database and source workbook.
Update STATUS/BACKLOG/CHANGELOG with dated evidence and distinguish unit, real
PostgreSQL, browser and deployment verification. Close only completed batches;
move this plan to completed only after its functional scope is validated.

## Progress

### Outcome

- R1-04: `a352312`, PR #3, merge `069323f`, 12 green CI checks; 111 PostgreSQL /
  11 Chromium cases at delivery.
- R1-03: `8a2169a`, PR #4, merge `400ce69`, 12 green CI checks; 150 PostgreSQL /
  11 Chromium cases. Viewer bypass and no-op version inflation fixed.
- R1-05: `c882e3d`, PR #5, merge `537fa9c`, push/PR CI green; 189 PostgreSQL /
  11 Chromium cases. Missing correlation, structured sensitive audit facts and
  revoked-resource activity disclosure corrected, without rewriting history.
- R1-02: final delivery on `codex/plan-006-r1-lifecycle`; four Chromium lifecycle
  journeys and four PostgreSQL identity/audit cases; suite now 193 PostgreSQL and
  15 Chromium cases. Exact association preservation checked. Production behavior
  required no further correction. GitHub CI and merge are recorded by the PR;
  only green-CI merge commits are authorized. No deployment acceptance is implied.
- Required quality gates and unit suites retained throughout. R1-06/R1-07 are
  prepared in BACKLOG with confirmed D2/D9; no new roadmap or host dependency.

### Earlier progress snapshots

- R1-03 integrated in PR #4, commit `8a2169a`, merge `400ce69`, 12 green CI checks.
- R1-05 active: audit mutation matrix, API request correlation, recursive credential
  redaction and current-visibility filtering of own recent activity. Scope and
  limitations documented in `docs/project/R1_05_AUDIT_COVERAGE.md`.

- R1-04 integrated via PR #3: commit `a352312`, merge `069323f`; all 12 CI checks
  passed. Expanded suggestion regression brings PostgreSQL total to 111.
- R1-03 implementation: 39 new PostgreSQL cases, viewer bypass and no-op version
  fixes; 150 integration and 11 existing Chromium cases pass. Quality gates and
  integration must be completed before moving to R1-05.

- 2026-10-31: activated; main merge verified locally; R1-04 regression tests added.
- 2026-10-31: R1-04 validated locally: format/lint/typecheck/unit checks, 91 real
  PostgreSQL tests and 11 Chromium E2E tests pass. Two hidden-ID leaks fixed;
  no schema or infrastructure changes. Implementation remains uncommitted on
  `codex/plan-006-r1-visibility`. Next batch: R1-03. Plan 006 remains active.
- Remaining work and validation evidence are maintained in `docs/project/STATUS.md`.
