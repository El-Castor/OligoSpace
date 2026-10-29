# Security model

## Identity and authorization

Keycloak is the OIDC provider. The web uses Authorization Code with PKCE and the
API validates issuer, audience, signature, expiration, and enabled-user state. The
OIDC subject maps to a local user record; passwords never enter OligoSpace.
Realm/client roles map to application roles, while team/project memberships scope
resource access. Every mutation is authorized in API services.

Local development supports a documented explicit bypass only when
`AUTH_MODE=development`; production rejects that value. Development identities are
marked in responses and must never be enabled in externally reachable deployments.

## Deployment controls

- HTTPS at Caddy; secure cookies and exact CORS origins.
- PostgreSQL/Redis private; MinIO console and Keycloak administration private.
- Secrets supplied outside Git, with startup validation in production.
- File size/type checks plus malware scanning integration point before publishing.
- API active-job limits per authenticated requester and institute for expensive
  scientific operations; infrastructure-level request throttling remains a deployment
  hardening item.
- Structured audit events exclude bearer tokens, cookies, secrets, and file bodies.

## Scientific worker controls

Scientific submission and retry authorization is enforced server-side. Viewers may
read results already visible to them but cannot consume compute. Job scope is derived
from the source record and cannot be broadened by clients; reads also require current
source access so a historical visibility snapshot cannot leak a narrowed record.

Celery messages contain only a job UUID and claim token. Primer3 is invoked with an
argument list and timeout, never a shell or arbitrary user option. Attempt diagnostics
and audit records contain stable IDs, digests, states and safe bounded errors—not
sequences, broker/database URLs, environment dumps, tokens or raw unrestricted logs.
The worker currently uses the application database credential in Compose; a separate
least-privilege PostgreSQL role is required before production deployment.

## Remaining hardening

Before production: threat model the chosen topology, configure institution-owned
DNS/TLS, rotate bootstrap credentials, enable MFA policy in Keycloak, add RLS
policies after permission tests, scan images/dependencies, and exercise incident and
restore runbooks. See `docs/project/BACKLOG.md`.
