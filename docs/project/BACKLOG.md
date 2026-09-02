# Backlog

## Now

- Review the deterministic Excel preview, target decomposition, and storage
  conflicts with a data owner; require explicit approval before import writes.
- Select and activate the next execution plan explicitly. Completing plan 003 does
  not automatically activate ExperimentRun/Validation or any later domain.

## Next

- ExperimentRun and contextual Validation with attachments.
- Persist and expose worker jobs/results for Primer3 QC and pair compatibility.
- Exact target-mapping persistence and interactive GeneOligoViewer.
- Inventory, orders, hierarchical locations, events, and QR workflows.

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

- Surface configurable Primer3 nearest-neighbor results from the worker while
  retaining existing Wallace calculation provenance.
- Generate TypeScript API types from OpenAPI after endpoint stabilization.
- Migrate to ESLint 10 when the Next.js lint plugin dependency graph supports it.
- Add isolated seeded fixtures per Playwright spec if parallel browser execution is
  enabled; the current independent specs run serially against persistent development data.
