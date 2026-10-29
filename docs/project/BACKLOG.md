# Backlog

## Now

- Human gates: authorize push of the Plan 005 branch (CI on the recovery fixes), then
  merge plans 002–005 into `main` with CI green.
- Candidate R1 batch (proposal from the 975a8ae audit, not approved): R1-04 visibility
  enforcement (AUTH-004/SEARCH-003), R1-03 Assay negative authorization matrix
  (ASSAY-004), R1-05 audit coverage without data leakage (AUDIT-001/002), R1-02
  lifecycle E2E.
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
- Fix pre-existing mypy errors on monkeypatches in the bioinfo-worker tests.
- Write a local-execution runbook for scientific jobs and the E2E stack.
- Generate TypeScript API types from OpenAPI after endpoint stabilization.
- Migrate to ESLint 10 when the Next.js lint plugin dependency graph supports it.
- Add isolated seeded fixtures per Playwright spec if parallel browser execution is
  enabled; the current specs run serially against one shared, ephemeral E2E stack.
