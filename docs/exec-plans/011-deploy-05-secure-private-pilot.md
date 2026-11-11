# DEPLOY-05 — Secure private pilot configuration

Owner supplied detailed execution specification; autonomous targeted reuse and
independent final review. Base origin/main36b0bf6 after PR22 merge; isolated
worktree, one branch/PR. No real deployment, provider adoption or release.

## Minimal audit and design

Reuse compose.pilot.json/policy/doctor/bootstrap/release, existing HTTPS OIDC and
scientific browser harnesses, DEPLOY04 Recovery. Existing topology has no runtime
resource hardening, external TLS trust inputs or semantic certificate preflight;
Keycloak production start is defined but prior OIDC qualification uses dev/H2.

Complete existing template with private canonical Caddy ingress, explicit external
certificates and trust, bounded nonroot services, health/log/stop controls, no
runtime builds/source binds/seed. Keep production digest approval separate from
local disposable immutable-image qualification. TLS templates and host diagnostic
must never fabricate real DNS/cert/supplier/scan/vault/offhost approval. Real
activation remains blocked by existing release gates and explicit AUTH-B6.

- [x] Extend resolved Compose/policy contracts and adversarial tests.
- [x] Add private HTTPS/production Keycloak configuration and trust checks.
- [x] Extend non-destructive doctor: explicit PASS/FAIL/BLOCKED/NOT_VERIFIED,
      local architecture/images/resources/permissions/schema and release blockers.
- [x] Reuse backup and migration/rollback maintenance contracts; no real executor.
- [ ] Real disposable production topology: HTTPS/PKCE/OIDC/MFA/permissions,
      bounded worker/science/BLAST, migrations/restart and DEPLOY04 recovery.
- [ ] Targeted tests then native ARM64/AMD64 CI, independent review/corrections.
- [x] DEPLOY05 report, STATUS/BACKLOG/CHANGELOG/runbook; sole PR, stopunmerged.

## Review focus

Reject untrusted proxy headers/alternate host/admin routes, missing secrets/weak
TLS, mutable/unapproved images, namespace overlap, broad worker grants, incomplete
qualification or fabricated PASS. Never cache revocation decisions. No app/JWKS
change in this lot; AUTH-B6 remains mandatory BLOCKED before pilot activation.

Independent review and corrections are complete; 128 deployment and 23 auth-runner
contracts pass. Full final-source native browser/scientific qualification remains
open: Ubuntu snapshot HTTP502/503 blocks image builds. Cached ARM64 component,
direct scientific and Recovery evidence is scoped separately in the report.
