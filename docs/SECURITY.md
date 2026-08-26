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
- Rate limits at proxy/API for authentication-sensitive and expensive operations.
- Structured audit events exclude bearer tokens, cookies, secrets, and file bodies.

## Remaining hardening

Before production: threat model the chosen topology, configure institution-owned
DNS/TLS, rotate bootstrap credentials, enable MFA policy in Keycloak, add RLS
policies after permission tests, scan images/dependencies, and exercise incident and
restore runbooks. See `docs/project/BACKLOG.md`.
