# MVP-02 — Scientific end-to-end acceptance

Base: `5e343407c8c998e7a8a844424bf90faba4b00272`.
Single branch: `codex/mvp-02-scientific-acceptance`; single PR, no merge.

## Scope and execution

Reuse the delivered registry, collaboration, CSV and Primer3 workflows. Qualify
them with synthetic data through production web/API, disposable PostgreSQL,
real HTTPS Keycloak and the pinned scientific worker. Preserve Scientific Soft UI,
personal files, scientific parameters and all DEPLOY-02 gates. No deployment,
release, provider adoption, uploads or additional export formats.

- [x] Inspect specifications, acceptance criteria, existing tests and branch state.
- [ ] Connect the seven existing scientific Chromium scenarios to an isolated OIDC
  harness with five identities in two organizations, worker and scheduler.
- [ ] Reproduce repeated-submission defects; verify minimal fixes against PostgreSQL.
- [ ] Execute reference values, persistence, rights/revocation, CSV and viewport checks.
- [ ] Run format, lint, typecheck, units, PostgreSQL/migrations, existing Chromium/OIDC.
- [ ] Independent review; fix demonstrated findings and rerun affected checks.
- [ ] Publish acceptance matrix/evidence/limitations, STATUS/BACKLOG/CHANGELOG,
  one PR and exact-head CI results. Stop for review.

## Review focus

Concurrent fresh idempotency keys must not produce 500s or duplicate active jobs.
Current source visibility must apply to stored results after permission removal.
Numerical comparisons must retain the validated reference parameters and units.
Scientific mode must not weaken or accidentally expand MVP-01 authentication tests.
Only synthetic evidence and sanitized diagnostics may leave the disposable stack.
