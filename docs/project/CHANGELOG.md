# Changelog

## Unreleased

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

### Changed

- Caddy now sends only `/api/v1/*` to FastAPI, preserves NextAuth `/api/auth/*`, and
  dynamically resolves recreated Compose containers.
- The standalone Next.js runtime listens on all container interfaces.
- Project reporting now distinguishes build verification, service/API runtime
  verification, and browser workflow verification.

### Validation

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

### Data quality

- Documented workbook placeholders, invalid/missing sequences, orientation
  normalization, length discrepancy, and duplicate storage positions without
  changing the source file.
- Recorded both observed source checksums after the workbook changed externally
  during the audit; the latest read-only preview supersedes stale missing-value
  observations while preserving their snapshot history.
