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

## Role and rights matrix

| Role | Identity/admin | Scientific resources | Membership management |
|---|---|---|---|
| admin | Provision explicit subjects, edit role/active; existing last-admin safeguards | Existing organization-scoped policies retained | Existing server-side policy |
| member (scientist) | Own profile; admin APIs denied | Create within permitted scope, read/edit according to owner/project/team policy | Project/team manager policy only; no global admin implied |
| viewer | Own profile; admin APIs denied | Read only within current visibility; mutation/compute denied | No privilege inferred from hidden controls |

team_manager remains an existing fourth scoped role, not removed by the three-role
acceptance fixture. Effective global role remains min(local role, OIDC role).
User active state and current team/project memberships are re-read on each API
call; cached frontend menus do not grant rights. Global admin is not cross-institute
access. Existing scientific visibility and permission tests are retained.

## Corrections and operational contract

1. Verify JWT locally before any introspection/identity lookup: RS256, signature,
   issuer, audience, expiration, iat and nonblank subject. Introspection must return
   boolean active=true; timeout/HTTP/provider/JSON failures deny access with safe401.
   Network timeout is5seconds; provider availability is now required per API call.
2. Bind stored provider to configured issuer. Existing literal keycloak mappings
   migrate to that issuer; a different stored provider is rejected before mutation.
   No email-based auto-linking, self-registration, invite, password storage or
   PostgreSQL schema migration was introduced.
3. Failed refresh removes usable access/refresh credentials and marks the session
   expired. A server-only logout credential remains in the encrypted NextAuth JWT
   so provider logout can be retried after a transient outage; it is never included
   in the browser session response. Browser access-token exposure is an existing
   contract preserved here, not a claim that bearer tokens are inaccessible to JS.
4. UserMenu first requests authenticated same-origin JSON POST provider logout.
   Failure retains the local session and shows a retry alert. Only confirmed logout
   proceeds to NextAuth's CSRF-protected signOut; the signOut event also attempts
   provider cleanup for direct NextAuth callers. Its warning contains a rule ID
   only. A direct NextAuth signOut alone is not provider-confirmation evidence.
5. Existing Compose configuration needed client credential forwarding to API and
   migration processes. The same existing outside-Git client ID/secret is wired;
   static policy now checks consistency/strength across API/migrate/web. No host,
   network, volume, image provider or deployed stack was changed.

### Configuration required before any pilot qualification

- API AUTH_MODE=oidc, OIDC_ISSUER canonical HTTPS, OIDC_AUDIENCE, OIDC_CLIENT_ID
  and OIDC_CLIENT_SECRET outside Git. Secret repr suppressed. Provider must allow
  confidential-client introspection and logout. No JWT-only fail-open fallback.
- Web AUTH_MODE=oidc, NEXTAUTH_URL canonical HTTPS, independent NEXTAUTH_SECRET,
  KEYCLOAK_ISSUER matching API issuer and matching confidential client credentials.
  PKCE S256/state/nonce and exact redirect URI; Secure/HttpOnly/Lax session cookies.
- Development realm file contains demo identities and is NOT an approved pilot
  import. Pilot must bootstrap institution-owned accounts and references explicitly,
  without demo users, default passwords or development authentication.
- Existing Keycloak reset-password feature requires mail delivery/operator policy
  qualification. No invitation/email delivery flow or Keycloak account creation
  UI exists in OligoSpace. Admin Create projection does not create a Keycloak user.
- Keycloak administration, MFA enrollment/recovery, issuer reachability/trust from
  browser and containers, secret rotation and outage/recovery remain operator gates.
  The fixture's synthetic TOTP flow is not institution-wide MFA-policy approval.

## Verification status and evidence attribution

Local API:85 passed,198 PostgreSQL cases skipped because no server was available;
33 new signed-token/introspection/identity/role-revocation cases included.
API Ruff/configured strict mypy pass. Web14 tests, strict typecheck and scoped lint
pass using temporary official-checksum-verified Node22.23.0. Existing cached
prototype/.next output requires a local lint exclusion only; CI uses clean source.
Infrastructure90 tests pass; Compose configuration passes. Combined make
format/lint/typecheck/test cannot reach local Docker daemon. Local Turbopack build
also hit a process/port permission error; no local build pass is claimed.
CI is authoritative for Docker builds, PostgreSQL and real Chromium/science.

Initial d95d3d5 application CI41539555372 passes; foundation startup failure from
missing introspection credentials was demonstrated and corrected in51399b8.
Current head qualification41540107580 and application CI are pending. No real
OIDC/MFA or screenshot acceptance is claimed until their sanitized artifacts are
available. Expected13 Chromium cases: actual login/cookies/PKCE/state/nonce,
forged state, admin projection, member/viewer denials, anonymous/bogus/development
headers rejected, invalid password, real refresh/provider logout, Keycloak disable,
project grant/revoke with old bearer, local disable and TOTP enrollment/challenge,
provider logout failure/retry. Skipped or absent tests are never successes.

Independent review found the credential-wiring and logout-failure regressions;
fixes and negative tests were added in the same PR. Final re-review pending.

## Remaining limitations and private-pilot decision

MVP-01 is not a deployment approval. Retain DEPLOY-02 security findings and all
release gates. No claim of validated real host, institutional SSO/federation,
mail delivery, MFA recovery, HA/Keycloak outage availability, or multiple concurrent
tab refresh-token rotation. Provider unavailable means fail closed, not continued
access. Review successful real-OIDC proofs and remaining security gates before any
private-pilot authorization. PR19 stays unmerged for user review.
