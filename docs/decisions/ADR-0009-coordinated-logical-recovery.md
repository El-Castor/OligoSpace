# ADR-0009 — Coordinated logical recovery

Status: proposed for code review; operational objectives and pilot approval pending.

## Context

Application PostgreSQL, PostgreSQL-backed Keycloak and S3 objects jointly define
recoverable scientific state. Independent dumps do not guarantee common state;
Redis is transport for DB-authoritative scientific jobs. Pilot hardware is limited.

## Decision

Use native logical dumps under verified stopped application/identity/ingress and
worker/scheduler writers, with exclusive external-writer maintenance fencing.
Capture current unversioned S3 objects through the existing SDK and selected
configuration. Preserve native ownership/ACL and require separately preprovisioned
roles/passwords. Verify all rows, attachment references and object bytes/metadata.
Wrap manifest/payload in streaming AES-256-GCM using the existing cryptography
library, random nonce and separate 256-bit operator key; private plaintext staging
requires an encrypted operator disk. Empty-target-only restore is journaled and
never starts writers automatically. Copy encrypted points to approved external
storage; authenticate before age/count retention. No schedule is installed.

## Alternatives and consequences

WAL/PITR alone cannot coordinate identity/S3 and adds operational complexity;
independent online snapshots are therefore not claimed. A full backup framework
would be a larger adoption than this bounded logical pilot path; a future
institution-approved pgBackRest repository can supersede it. Realm JSON alone
loses identity state; internal S3 disk copies couple recovery to a provider.

Downtime, temporary disk amplification and same-major PostgreSQL restoration are
accepted *technical limitations*, not owner-approved RPO/RTO. Version history,
object lock/SSE, policy/lifecycle/replication and actual vault/off-host continuity
remain explicit operational gates. Revisit for measured capacity/downtime failure,
versioned storage, lower RPO, multi-writer topology or institutional backup adoption.
No security finding or supplier decision is waived by this ADR.
