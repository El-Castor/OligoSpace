# Backlog

## Now

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
