# OligoSpace architecture

## Purpose

OligoSpace is a modular monorepo with a TypeScript web client, a Python API, a
Python-first computation worker, PostgreSQL, Keycloak, Redis, and S3-compatible
object storage. It starts as a modular monolith plus worker so boundaries are clear
without premature distributed-system complexity.

```text
Browser -> Caddy -> Next.js web -> FastAPI -> PostgreSQL
                    |              |  |
                    |              |  +-> MinIO (attachment metadata in DB)
                    |              +----> Redis -> bioinfo worker
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
  asynchronous jobs, search, import/export, and stable identifiers.
- Scientific services: sequence normalization/QC, duplicate detection, exact target
  mapping, and later Primer3/BLAST adapters.

PostgreSQL is authoritative. Identity credentials stay in Keycloak; the database
stores the OIDC subject and collaboration profile. Large files live in object
storage. Dynamic method-specific fields may use validated JSONB; core relations do
not.

See `docs/DATA_MODEL.md` and ADRs for rationale. The completed first milestone is
recorded in `docs/exec-plans/completed/001-initial-mvp.md`.
