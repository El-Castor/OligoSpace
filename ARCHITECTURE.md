# OligoSpace architecture

## Purpose

OligoSpace is a modular monorepo with a TypeScript web client, a Python API, a
Python-first computation worker, PostgreSQL, Keycloak, Redis, and S3-compatible
object storage. It starts as a modular monolith plus worker so boundaries are clear
without premature distributed-system complexity.

```text
Browser -> Caddy -> Next.js web -> FastAPI -> PostgreSQL
                    |              |  |          ^
                    |              |  +-> MinIO  | scientific result commit
                    |              +----> Redis -> bioinfo worker
                    |                         ^          |
                    |                         +-- Celery Beat reconciler
                    +-> Keycloak OIDC <--- JWT validation / role mapping
```

Only the reverse proxy is public in production. PostgreSQL, Redis, MinIO's admin
interface, and Keycloak's administration interface remain on private networks.

## Application boundaries

- Registry: organizations, teams, projects, organisms, reference genomes, targets,
  oligos, experiment types, assays, and contextual assay-oligo roles.
- Laboratory: experiment runs, contextual validations, orders, synthesized lots,
  aliquots/stock items, hierarchical locations, and immutable inventory events.
- Platform: identity projection, RBAC/visibility, audit events, attachments,
  persistent scientific jobs, search, import/export, and stable identifiers.
- Scientific services: sequence normalization/QC, duplicate detection, exact target
  mapping, qualified Primer3 thermodynamics, and later BLAST adapters.

PostgreSQL is authoritative. Identity credentials stay in Keycloak; the database
stores the OIDC subject and collaboration profile. Large files live in object
storage. Dynamic method-specific fields may use validated JSONB; core relations do
not.

## Persistent scientific-job boundary

FastAPI validates the subject, permissions, parameter allow-list, immutable sequence
snapshot, and idempotency key before committing a queued `ScientificJob`. Redis carries
only the job UUID and claim token. The worker reloads authoritative inputs from
PostgreSQL, appends a leased attempt, invokes the pinned Primer3 executables without a
shell, and atomically persists the immutable result and terminal state. Celery results
are operational only; browser reloads always read PostgreSQL.

Celery Beat reconciles committed jobs that were not published, retryable jobs whose
delay elapsed, and expired worker leases. The worker and scheduler share one runtime
image. Small structured inputs/results remain in validated JSONB; Plan 005 introduces
no second result store and does not use MinIO.

See `docs/DATA_MODEL.md` and ADRs for rationale. The completed first milestone is
recorded in `docs/exec-plans/completed/001-initial-mvp.md`.
