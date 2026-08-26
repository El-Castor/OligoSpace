# ADR-0003: Keycloak-managed identity

- Status: accepted
- Date: 2026-08-25

## Context

External access and future institutional SSO require mature authentication, MFA,
account disablement, and federation without application-managed passwords.

## Decision

Use Keycloak over OIDC Authorization Code with PKCE. Validate access tokens in the
API and project the stable OIDC subject to an application user. Authorization and
visibility remain application concerns.

## Alternatives

Homemade password authentication carries unacceptable maintenance and security
risk. SaaS identity would introduce institutional data/control dependencies.

## Consequences

Local development requires realm bootstrap configuration. Production operators must
secure administration, configure federation/MFA, rotate bootstrap secrets, and
align token claims with OligoSpace roles.
