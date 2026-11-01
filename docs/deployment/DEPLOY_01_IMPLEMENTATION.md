# DEPLOY-01 — Reproducible deployment foundation

Status: in progress, not a deployable release. PR16 merged at
`ab0ec42144dbc34629b2675cc67b4364d5abc820`; no Mac mini contacted.

## Execution plan and boundaries

Spec: user DEPLOY-01 request and PILOT_HOSTING_PLAN.md. Implementation stays on
`codex/deploy-01-reproducible-foundation`. No scientific/frontend logic change.
Use inline execution with isolated, explicitly named disposable test resources.

- [ ] A/B: inventory existing dependencies and startup; storage evidence/decision.
- [ ] C/F: independent pilot Compose and fail-closed static policy, negative tests.
- [ ] D: release image build/manifest contract, architecture evidence and limits.
- [ ] E/G: prepare bootstrap/update and verify PostgreSQL/migration in isolation.
- [ ] H: diagnostic/install contract, regression tests, independent review, PR/CI.

Storage substitution is not authorized implicitly. An unavailable/unmaintained
artifact leaves the storage gate blocked; this must not produce a ready release.
No production digests, secrets, names or security acceptance will be invented.
