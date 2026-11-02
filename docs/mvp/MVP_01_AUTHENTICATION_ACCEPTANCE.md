# MVP-01 — Authentication acceptance

Status: implementation/qualification in progress; no pilot approval.
Base main:5e10b750889275a0db76a94fdb1e85c83f95e88b (DEPLOY-02 merge).
One branch/PR only; no deployment, provider substitution or security waiver.

## Existing implementation and bounded plan

Keycloak Authorization Code+PKCE/state; NextAuth encrypted JWT session and refresh;
FastAPI RS256/issuer/audience/exp/iat/sub validation. Local provisioned user must
exist and be active; strongest allowed role is the lower of token/local roles.
Memberships are read from PostgreSQL on every API request. Admin UI/API already
create projections, enable/disable accounts and manage roles and memberships.
No self-registration or app-managed password. Keycloak reset-password is enabled
in the development realm, but no mail delivery/invitation qualification exists.
Preserve explicit subject provisioning; never associate by email automatically.

Demonstrated gaps to qualify/fix: JWT signature alone cannot observe Keycloak
logout/disable while a token is unexpired; logout currently removes browser session
and redirects without server-side invalidation; refresh failure retains old access
token. Add confidential-client introspection after cryptographic validation,
fail closed on unavailable/inactive provider, and bind local provider identity.
Keep JWT credentials server-side except existing access-token session contract;
never expose refresh tokens. Add provider logout via server-side NextAuth signOut
using its CSRF-protected endpoint. No schema/business policy rewrite.

## Execution and acceptance steps

- [ ] Negative/positive API tests for crypto claims, provider active/revoked/down,
  local active/provisioning/provider binding, role and project permission changes.
- [ ] Backend minimal fixes with bounded async introspection, production settings
  validation; frontend refresh/logout failure handling tests.
- [ ] Isolated real Keycloak/PostgreSQL/Next.js/API Chromium fixture, AUTH_MODE=oidc,
  HTTPS, synthetic admin/member/viewer, PKCE/state, cookies, refresh, expiry,
  provider/local revocation, roles/direct API denial, logout and MFA.
- [ ] Preserve unit/PostgreSQL/scientific and existing Chromium regressions;
  capture only synthetic safe screens, never cookies/tokens/raw HTTP traces.
- [ ] Final matrix/results/limits, independent review, backlog/memory and one PR.

## DEPLOY-02 integration boundary

Owner authorized integration only of7c81574, merged5e10b75. Residual Debian and
supplier findings remain visible and release-blocking; no acceptance for real use.
Reexamine2026-11-16 or earlier on fix/new risk. Priority security follow-up:
evaluate minimal/alternative Debian13 API/worker images preserving Python,
Primer3, BLAST and native ARM64/AMD64 reproducibility. Not implemented in MVP-01.
