# OligoSpace

OligoSpace is a collaborative platform to design, register, validate, share,
locate, and reuse primers, probes, oligonucleotides, and experimental assays across
research teams.

The project is deliberately honest about its maturity. The current milestone is a
browser-verified, containerized core registry: model/API, OIDC boundary, scientific
sequence services, migration preview, and usable oligo/target/assay workflows.
Inventory, experiment validation, attachments, global search, gene visualization,
and production backup automation are designed and tracked but not yet complete.

## Why the model matters

OligoSpace separates facts that a spreadsheet tends to mix:

- an `Oligo` is a biological sequence identity;
- an `AssayOligo` gives that sequence a role in a reusable `Assay`;
- an `ExperimentRun` is an execution, with contextual `Validation` evidence;
- an `OligoLot` and `StockItem` represent synthesized material and tubes;
- inventory history is append-only and physical location is hierarchical.

See [ARCHITECTURE.md](ARCHITECTURE.md),
[the data model](docs/DATA_MODEL.md), and [project status](docs/project/STATUS.md).

## Current features

- FastAPI/SQLAlchemy registry foundation for users, teams, projects, organisms,
  reference genomes, targets, experiment types, oligos, assays, contextual roles,
  stable IDs, visibility, and audit events.
- Sequence normalization, validation, GC%, Wallace screening Tm, unmodified ssDNA
  molecular-weight estimate, reverse complement, duplicate classification, and exact
  target mapping with ambiguity reporting.
- Preview-only Excel migration framework and an evidence-backed report for the
  existing workbook; the source is never modified.
- Next.js research workspace with dashboard, oligo/target/assay search, create,
  detail, and authorized edit workflows, contextual assay roles, global core search,
  responsive navigation, truthful empty states, and Keycloak session integration.
- Compose stack for web/API/worker/PostgreSQL/Redis/Keycloak/MinIO/Caddy, plus seed,
  migration, CI, and guarded backup/restore-test scaffolds.

## Local container setup

Requirements: Docker with Compose v2 and a hostname resolver that maps
`*.localhost` to loopback (current browsers/operating systems generally do).

```bash
make dev-env
docker compose up --build
```

Open `http://oligospace.localhost:8080`. The environment generator prints the
temporary `local-admin` Keycloak password and writes secrets to a mode-0600 `.env`
that Git ignores. Development mode bypasses interactive login by default; set
`AUTH_MODE=oidc` to exercise Keycloak. Never copy local credentials to production.

The first image build downloads pinned dependencies and may take several minutes.
PostgreSQL, Redis, MinIO, and Keycloak administration have no public host ports.

## Conda development

```bash
conda env create -f envs/api.yml
conda env create -f envs/bioinfo.yml
conda activate oligospace-api
pip install --no-deps -e apps/api
```

Use Node 20.9+ and npm for `apps/web`; Node is intentionally outside
Conda. Important commands are:

```bash
make format
make lint
make typecheck
make test
make test-integration
make test-e2e
make compose-config
```

If the named Conda environments or Node are not installed, run the same checks with
the pinned container toolchains:

```bash
make format lint typecheck test PYTHON_RUNNER=container
```

`PYTHON_RUNNER=conda` (default) uses the `oligospace-api` and `oligospace-bioinfo`
environments plus host npm; `PYTHON_RUNNER=container` builds the
`oligospace-*-tooling` images and mounts the checkout read-write for formatting.
Neither runner touches a database: PostgreSQL-backed tests are skipped by
`make test` and run by `make test-integration`, which uses a throwaway tmpfs
`postgres-test` service, round-trips Alembic (`upgrade head` → `downgrade
0003_experiment_evidence` → `upgrade head`), and fails if any integration test is
skipped.

`make test-e2e` runs Playwright against a separate Compose project
(`oligospace-e2e`, `compose.e2e.yml`, including the scientific worker and
scheduler) configured only from the public placeholders
in `infra/e2e/e2e.env`. It never reads `.env`, publishes no host port, stores
PostgreSQL, Redis, MinIO, and Caddy state on tmpfs, tags its images
`oligospace-e2e-*`, and removes its containers and volumes when it finishes. Dev
data, volumes, and images are never shared with it; never point E2E tests at real
experimental data.

Preview the immutable source workbook with:

```bash
make import-oligos SOURCE=/absolute/path/Oligo_database_CP.xlsx
```

This command only emits a preview. It does not write to PostgreSQL.

## Security and operations

Keycloak owns credentials and future institutional federation. The API validates
OIDC tokens and enforces RBAC/visibility server-side. Caddy is the only intended
public ingress; secrets stay outside Git. Production requires institution-owned
DNS/TLS, MFA/SSO policy, secret management, security review, and removal of all
development modes. See [SECURITY.md](docs/SECURITY.md) and
[DEPLOYMENT.md](docs/DEPLOYMENT.md).

Backups use PostgreSQL-aware archives now and are designed to progress to encrypted
pgBackRest/WAL repositories with INRAE-controlled pull replication. A backup is not
accepted until restored and smoke-tested; see
[BACKUP_RESTORE.md](docs/BACKUP_RESTORE.md).

## Roadmap

The ordered roadmap and known gaps live in [BACKLOG.md](docs/project/BACKLOG.md).
Completed execution plans are
[001-initial-mvp.md](docs/exec-plans/completed/001-initial-mvp.md) and
[002-core-registry-workflows.md](docs/exec-plans/completed/002-core-registry-workflows.md).
No later phase is active until its execution plan is explicitly activated.
