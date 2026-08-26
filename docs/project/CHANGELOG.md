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

### Validation

- Passed formatting, lint, strict Python/TypeScript type checks, 15 API tests,
  2 real Primer3 worker tests, web smoke test, and Next.js production build.
- Applied `0001_initial_registry` and 17 seed records to isolated PostgreSQL 17;
  removed the temporary validation stack after verification.
- Regenerated the read-only Excel preview with an unchanged source checksum.

### Data quality

- Documented workbook placeholders, invalid/missing sequences, orientation
  normalization, length discrepancy, and duplicate storage positions without
  changing the source file.
- Recorded both observed source checksums after the workbook changed externally
  during the audit; the latest read-only preview supersedes stale missing-value
  observations while preserving their snapshot history.
