# Disposable real OIDC qualification

Run `python3 infra/auth-qualification/run.py` on an Ubuntu Docker host with
Compose v2 and OpenSSL. This builds the production Next.js/API images and the
repository-pinned Chromium runner. It needs no environment file or account.

The dedicated randomly named Compose project contains tmpfs PostgreSQL, Keycloak
26.7.2, API in `ENVIRONMENT=production` / `AUTH_MODE=oidc`, production Next.js and
Caddy HTTPS. No host ports, real records, MinIO or worker are used. Uploads are
disabled. Keycloak uses its disposable development server and embedded store;
this qualifies the real OIDC protocol and policy, not a production Keycloak
installation, institutional directory, hosted TLS or availability architecture.

One canonical issuer (`https://auth-qualification.test/realms/qualification`) is
reachable by API, web and Chromium on the disposable Docker network. A generated
one-day self-signed CA/server certificate is trusted explicitly by Node/Python;
Chromium alone ignores certificate trust errors. No application disables TLS
verification. Keycloak's administration endpoint is internal only.

All passwords, client/session secrets, subjects and bootstrap projections are
generated for the run. They exist only in a temporary directory removed on exit,
or process/container memory. No development seed is loaded. Keycloak identity
credentials and the four approved initial database projections are synthetic;
the pending identity is subsequently provisioned through the application UI.
MFA is tested by real TOTP enrollment and the next-login challenge.

The runner checks PKCE/state/nonce, cookie flags, rejected forged state, persistent
identity and roles, UI provisioning, negative direct API authorization, project
membership grant/revocation, cross-organization isolation, local deactivation, real token refresh, provider
logout, disabled-user introspection and failed refresh. Tests
have no skip path. Runtime failures fail the command; no static check is reported
as a successful browser qualification. All sixteen cases must pass, including
a provider-logout failure that preserves the local session followed by a
confirmed retry that revokes the already issued bearer token.

The harness first runs the unchanged real-login case as a bounded preflight.
If that fails, it retains its diagnostics, labels each remaining case
`not_executed`, cleans up, and fails. If it passes, the complete sixteen-case
suite runs; only all sixteen successful results qualify the run.

The final log gate reads complete API, web, Keycloak and Caddy logs only in RAM,
with a 4 MiB and 30-second limit per service. It checks every generated password
and application secret plus JWT-shaped material. Findings fail qualification;
retrieval errors or exceeded limits produce `not_verified` and also block
success. `secret-log-gate.json` contains only service names, fixed rule/category
identifiers, counts and gate outcomes. Raw logs and matched values are never
retained. An already failed preflight keeps its failure while retaining this gate.

Three cases extend the original login/revocation proof. One compares two real Keycloak
administrators in different organizations on direct API and UI access. One measures
`/health/live` (no authentication), `/me` (JWT validation, per-request introspection
and database re-read) and direct Keycloak introspection at concurrency 1, 4, 8 and 16
with 80 requests per phase; any refusal of a valid token fails the case. One asks the
harness, through two empty signal files, to stop then start only the disposable Keycloak
service while an already issued unexpired access token is replayed: every request must
be refused (no cached acceptance) and a fresh login must work after recovery. The
browser container receives the disposable client secret only to time direct
introspection; no result field is free text, and `introspection-load.json` and
`keycloak-outage.json` are copied only when they match a strict numeric schema.

The ignored `evidence/` directory receives a sanitized JSON summary and two
deliberate synthetic dashboard/administration captures. The workflow retains
these as an artifact even on failure. MFA enrollment is never captured.

No raw container logs, HTTP bodies, tokens, callback URLs, Playwright traces,
videos, HARs or error stacks are retained. The custom reporter emits only fixed
test titles/statuses, and orchestration suppresses subprocess output. A failed
phase is reported without credential material. Troubleshoot in the same disposable
environment with care; do not publish its logs. The project is removed in a
`finally` block; an abruptly killed process may require removal of only the
`oligospace-oidc-*` project from that run.
