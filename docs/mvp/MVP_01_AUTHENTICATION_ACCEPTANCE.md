# MVP-01 — Authentication acceptance

Status: delivered for review (PR19, DRAFT, unmerged); real-OIDC qualification 13/13
passed at 0c58d62; no pilot approval. Conditions for a private pilot are listed below.
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

- [x] Negative/positive API tests for crypto claims, provider active/revoked/down,
  local active/provisioning/provider binding, role and project permission changes.
- [x] Backend minimal fixes with bounded async introspection, production settings
  validation; frontend refresh/logout failure handling tests.
- [x] Isolated real Keycloak/PostgreSQL/Next.js/API Chromium fixture, AUTH_MODE=oidc,
  HTTPS, synthetic admin/member/viewer, PKCE/state, cookies, refresh, expiry,
  provider/local revocation, roles/direct API denial, logout and MFA.
- [x] Preserve unit/PostgreSQL/scientific and existing Chromium regressions;
  capture only synthetic safe screens, never cookies/tokens/raw HTTP traces.
- [x] Final matrix/results/limits, independent review, backlog and one PR.
  ResearchBrain/Basic Memory was not reachable from this session: not updated (see
  Remaining limitations).

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

Local API:99 passed,198 PostgreSQL cases skipped because no server was available
(local only; the PostgreSQL suites pass in CI, see below);
47 new signed-token/introspection/identity/role-revocation cases included.
API Ruff/configured strict mypy pass. Web14 tests, strict typecheck and scoped lint
pass using temporary official-checksum-verified Node22.23.0. Existing cached
prototype/.next output requires a local lint exclusion only; CI uses clean source.
Infrastructure90 tests and7 qualification guard tests pass; Compose configuration passes. Combined make
format/lint/typecheck/test cannot reach local Docker daemon. Local Turbopack build
also hit a process/port permission error; no local build pass is claimed.
CI is authoritative for Docker builds, PostgreSQL and real Chromium/science.

## Final results (head 0c58d62)

Real-OIDC qualification (run 41549959570, disposable HTTPS Keycloak 26.7.2, PostgreSQL,
production Next.js and API, Chromium, AUTH_MODE=oidc): **13/13 passed**, artifacts in
[evidence/](evidence/summary.json). Application CI (runs 41549959456 and 41549952778)
passes: backend, integration (PostgreSQL), migration, bioinfo-worker, frontend,
compose, deployment-contract, and the existing scientific/functional Chromium job
(`chromium`, run 41549959418). Secret/token log gate: passed for api, web, keycloak, caddy
([secret-log-gate.json](evidence/secret-log-gate.json)). API rule counters for the
run: introspection inactive 4 (expected revocations), JWT claims invalid 1 (the
bogus-token journey), signature/JWKS/transport/HTTP/JSON failures 0.

Red checks on the PR are exclusively DEPLOY-02 vulnerability/supplier gates
(baseline-secret-triage, native-image api/worker, seaweedfs, garage). They fail by
scan exit code 2 on documented findings, do not touch authentication, are not waived
and remain release-blocking. They do not run on `main`.

| # | Journey (real provider) | Result |
|---|---|---|
| 1 | Login with PKCE S256, state, nonce; Secure/HttpOnly/Lax cookies | passed |
| 2 | Callback with forged state yields no session | passed |
| 3 | Unprovisioned identity gets 403 + recovery screen; admin provisions; login then works | passed |
| 4 | Member: admin APIs 403 (read and write), /admin denied | passed |
| 5 | Viewer: admin APIs 403, project creation 403, /admin denied | passed |
| 6 | Anonymous, malformed and development-header requests 401 | passed |
| 7 | Wrong password creates no session | passed |
| 8 | Project grant then revoke apply to the same issued token (200 then 404) | passed |
| 9 | Local deactivation: already-issued valid token gets 403; recovery screen; logout | passed |
| 10 | Provider logout failure keeps session and shows retry; confirmed retry revokes token (401) and SSO | passed |
| 11 | Access token refresh; logout ends provider SSO | passed |
| 12 | Keycloak account disabled: issued token 401, refresh fails, session marked expired | passed |
| 13 | TOTP enrollment then MFA challenge, invalid then valid code | passed |

Login/logout/refresh/revocation flow: login = Authorization Code + PKCE through
Keycloak; API verifies JWT then introspects per call; refresh by NextAuth server side
(a failed refresh drops usable credentials); logout = same-origin CSRF-checked POST
to the provider-logout route, then NextAuth signOut only after provider confirmation;
revocation = provider disable (introspection inactive) or local `active=false`
(403) or membership removal (404), all effective on tokens already issued.

A first qualification run at 22ba4c9 passed 11/13; the two failures (journeys 3 and 9)
were a test race, not a product defect: after "Manage session" the page is already on
`/login`, so the URL assertion passed before logout finished and the session was read
too early. The test now polls until the session is ended, and also proves provider SSO
ended by requiring the Keycloak password form on the next login. No product code
changed for that fix; the failing result is retained here, not hidden.

### Screens (synthetic data only, no cookies/tokens/URLs with codes)

![Login](evidence/synthetic-login.png)
![Administrator overview](evidence/synthetic-dashboard.png)
![User administration](evidence/synthetic-administration.png)

The administration capture shows the issuer URL stored for the identity that already
logged in, versus the literal `keycloak` for projections not yet bound; the latter is
migrated to the configured issuer at first successful login.

## Independent review (read-only, separate agent, final head)

Confirmed: RS256-only with signature/issuer/audience/exp/iat/sub checks, fail-closed
introspection with 5 s timeout, development headers ignored under oidc, production
settings validation, subject-keyed identity without email linking, per-request active
and role re-read, organization-scoped access checks, logout origin/content-type check,
no refresh token in the browser session, no secrets in repository or logs gate.

Findings and disposition:
- Reported as major: "last admin can be disabled". Verified partly incorrect: the acting
  administrator can never disable or demote themself (`cannot_remove_own_admin_access`),
  so the actor remains an active admin. Only a concurrent mutual demotion by two
  administrators is not serialized. Retained as a backlog item (AUTH-B1), not a
  silent change to existing business policy in this PR.
- Minor: legacy `keycloak` provider literal is accepted and rebound to the issuer.
  Intentional, documented migration; a different issuer is rejected. Backlog AUTH-B2
  to retire the literal after pilot bootstrap.
- Minor: email/display name are refreshed from validated claims on each request.
  Accepted: claims come from a signature- and introspection-verified token; no
  authorization decision uses them. Backlog AUTH-B3 (audit on change).
- Not covered by tests (stated, not claimed): cross-organization negative journey in
  real OIDC (covered only by existing API tests), concurrent logout/refresh race,
  multi-tab refresh-token rotation, issuer change scenario.

Independent review found the credential-wiring and logout-failure regressions
(earlier pass); fixes and negative tests were added in the same PR. Final
re-review: see section above.

## Remaining limitations and private-pilot decision

Missing or out-of-scope features (explicit, none added in this PR): invitation by
email, account creation in Keycloak from OligoSpace, self-registration, password
reset qualification (Keycloak feature exists, mail delivery unqualified), MFA
recovery policy, institutional SSO/federation, session listing/forced remote logout
for all of a user's sessions from the OligoSpace UI. Proposing any of these is a
separate product decision awaiting the owner.

Conditions for a private pilot (all must hold, none is granted by this PR):
1. Owner decision on this PR and on the open DEPLOY-02 release gates (reexamine
   2026-11-16 or earlier).
2. Institution-owned Keycloak realm bootstrapped without demo identities, default
   passwords or `AUTH_MODE=development`; confidential client secret rotated and held
   outside Git; HTTPS issuer reachable and trusted by browser and containers.
3. Operator procedure for MFA enrollment/recovery, reset-password mail delivery,
   Keycloak outage (API fails closed) and account offboarding (disable in Keycloak and
   local projection).
4. Re-run of the real-OIDC qualification against the pilot topology (all 13 journeys)
   plus a cross-organization negative journey, before any real use.
5. Backlog items AUTH-B1..B3 reviewed.

ResearchBrain/Basic Memory was not available in this session (no tool exposed), so
no memory note was written; the owner should record the outcome from this dossier.

MVP-01 is not a deployment approval. Retain DEPLOY-02 security findings and all
release gates. No claim of validated real host, institutional SSO/federation,
mail delivery, MFA recovery, HA/Keycloak outage availability, or multiple concurrent
tab refresh-token rotation. Provider unavailable means fail closed, not continued
access. Review successful real-OIDC proofs and remaining security gates before any
private-pilot authorization. PR19 stays unmerged for user review.

## Diagnosed real-provider failures (not waived)

The initial real-provider run was not a success: valid-shaped tokens were rejected
with401. Controller0840521 preflight retained all expected structural booleans,
three OIDC_INTROSPECTION_INACTIVE events and zero JWT/JWKS/transport failures.
Keycloak26.7.2 [verifyAudience source](https://github.com/keycloak/keycloak/blob/26.7.2/services/src/main/java/org/keycloak/protocol/oidc/AccessTokenIntrospectionProvider.java#L273)
requires the authenticated introspection client to be an access-token audience.
The existing configuration minted oligospace-api audience only but authenticated
introspection as oligospace-web. An explicit second audience mapper for the
existing web client corrects this contract. API audience remains oligospace-api;
no issuer, signature, audience check or introspection enforcement is disabled.
The API and web are the two components of the same existing confidential-client
integration; a separately credentialed resource-server client would be a future
institutional design choice, not silently introduced here.

The original forged-state test also failed to intercept its intended redirect
(interception_seen=false); it did not demonstrate a bypass. The corrected test
alters Keycloak's actual form-response redirect and requires interception plus
absence of an application session. No state/code/URL is retained.
A failed login preflight now labels the other12 journeys not_executed and fails;
all13 must pass in a complete run. Log verification reads bounded service output
in RAM only; actual matches fail, incomplete/truncated reads are not_verified.
