# Requirements traceability

This matrix maps every canonical requirement in `PRODUCT_SPEC.md` to current
implementation and evidence. Status describes the whole acceptance statement, not
merely the presence of a model or a successful build.

- **Planned:** accepted scope, no meaningful implementation yet.
- **In progress:** partially implemented or awaiting required verification.
- **Implemented:** implementation exists but lacks sufficient test/runtime evidence.
- **Verified:** a relevant automated test or recorded runtime validation passes.
- **Blocked:** an external decision, dataset, endpoint, or authorization is required.

Paths are repository-relative. `001` and `002` mean the completed execution plans
in `docs/exec-plans/completed/`.

## Identity and collaboration

| Requirement ID | Status | Relevant code/module | Tests or runtime evidence | Execution plan |
|---|---|---|---|---|
| AUTH-001 | Implemented | `apps/web/lib/auth.ts`, `app/api/auth/[...nextauth]`, Keycloak realm | OIDC browser flow not yet exercised | 001, 002 |
| AUTH-002 | In progress | API/web development auth and production config guard | Development identity verified by Caddy E2E; production guard untested | 001, 002 |
| AUTH-003 | In progress | `domain/permissions.py`, registry services | `test_permissions.py`; PostgreSQL core-registry 403 integration | 001, 002 |
| AUTH-004 | In progress | visibility enums, `repositories/registry.py` | `test_permissions.py`; core visible-query integration only | 001, 002 |
| AUTH-005 | Implemented | `security/auth.py`, CORS, Caddy headers | No end-to-end OIDC/security test | 001 |
| USER-001 | Implemented | `models/registry.py::User`, `/auth/me` | Build/static validation only | 001 |
| USER-002 | Implemented | active-user check in `security/auth.py` | No disabled-account integration test | 001 |
| USER-003 | In progress | dashboard summary and `apps/web/app/page.tsx` | Dashboard verified by Caddy E2E; saved views/alerts absent | 001, 002 |
| TEAM-001 | Planned | Team model only | — | Backlog |
| TEAM-002 | In progress | TeamMembership model and visibility policy | `test_permissions.py`; no management workflow | 001, Backlog |
| TEAM-003 | Planned | Navigation placeholder only | — | Backlog |
| PROJECT-001 | Planned | Project model only | Migration application in 001 | Backlog |
| PROJECT-002 | In progress | ProjectMembership and permission policy | `test_permissions.py`; no management workflow | 001, Backlog |
| PROJECT-003 | In progress | project foreign keys on core entities | Migration application; no project workflow | 001, Backlog |
| PROJECT-004 | Planned | Navigation placeholder only | — | Backlog |

## Scientific registry

| Requirement ID | Status | Relevant code/module | Tests or runtime evidence | Execution plan |
|---|---|---|---|---|
| ORGANISM-001 | In progress | organism model and admin list/create routes | Migration/seed validation; no UI/catalog tests | 001, Backlog |
| ORGANISM-002 | Implemented | organism foreign keys on target/genome/assay | PostgreSQL schema validation only | 001 |
| GENOME-001 | Implemented | `ReferenceGenome` model and migration | PostgreSQL migration validation | 001 |
| GENOME-002 | In progress | checksum/version fields; mapping services | `test_target_mapping.py`; no governed reference runtime | 001, Backlog |
| GENOME-003 | Planned | — | — | Backlog |
| TARGET-001 | Verified | target API/services and web create form | PostgreSQL create integration; Caddy create/detail E2E | 002 |
| TARGET-002 | In progress | target schema/form avoids inference | Sequence normalization tests; source provenance incomplete | 002, Backlog |
| TARGET-003 | In progress | target search/detail/update/status and audit | Caddy create/detail/edit/reload E2E; deprecate/archive path untested | 002 |
| TARGET-004 | Planned | target/assay FK only | — | Backlog |
| OLIGO-001 | Verified | oligo API/services and web create/detail forms | PostgreSQL route integration; Caddy create/detail/reload E2E | 001, 002 |
| OLIGO-002 | Verified | update schema forbids sequence; edit form read-only | PostgreSQL PATCH sequence rejection | 002 |
| OLIGO-003 | Verified | `sequence_analysis.py`, create service | `test_sequence_analysis.py`; PostgreSQL normalization integration | 001, 002 |
| OLIGO-004 | Verified | sequence metrics service and detail UI | `test_sequence_analysis.py`; PostgreSQL response validation | 001, 002 |
| OLIGO-005 | Verified | `calculation_provenance` and provenance UI | Unit assertions plus PostgreSQL serialized response | 001, 002 |
| OLIGO-006 | Verified | duplicate/reverse-complement checks | sequence duplicate unit tests; PostgreSQL exact-duplicate integration | 001, 002 |
| OLIGO-007 | In progress | list/search/detail/edit/status routes and pages | PostgreSQL search/update/audit and Caddy list/detail/edit/reload; archive path untested | 002 |
| EXPTYPE-001 | In progress | model, seed, admin routes | 17-row seed runtime validation; no management UI | 001, Backlog |
| EXPTYPE-002 | In progress | assay role validation | PostgreSQL valid-role integration; required metadata not enforced | 001, 002 |
| EXPTYPE-003 | Implemented | active filter and restrictive assay FK | Migration/schema validation only | 001 |
| ASSAY-001 | Verified | assay create/search/detail/edit API and pages | PostgreSQL route integration; Caddy create/detail/reload E2E | 001, 002 |
| ASSAY-002 | Verified | `AssayOligo`, contextual-role form | PostgreSQL association integration; Forward/Reverse Caddy E2E | 001, 002 |
| ASSAY-003 | Implemented | separate Oligo/AssayOligo/Assay models | ADR-0004 and schema validation | 001 |
| ASSAY-004 | Implemented | `_validate_assay_references` | Valid association integration; negative matrix incomplete | 001, 002 |
| ASSAY-005 | Verified | expected product/amplicon API and UI | Expected amplicon asserted by Caddy E2E | 002 |
| ASSAY-006 | Verified | version increment and before/after audit | PostgreSQL version/audit integration | 002 |
| ASSAY-007 | In progress | search/detail/edit/status workflows | PostgreSQL API and Caddy edit/version/reload E2E; archive path untested | 002 |

## Experiment evidence and attachments

| Requirement ID | Status | Relevant code/module | Tests or runtime evidence | Execution plan |
|---|---|---|---|---|
| EXPRUN-001 | Planned | — | — | Backlog |
| EXPRUN-002 | Planned | — | — | Backlog |
| EXPRUN-003 | Planned | — | — | Backlog |
| VALID-001 | Planned | domain separation documented | — | Backlog |
| VALID-002 | Planned | — | — | Backlog |
| VALID-003 | Planned | — | — | Backlog |
| VALID-004 | Planned | ExperimentType hints seeded | — | Backlog |
| ATTACH-001 | Planned | MinIO infrastructure only | — | Backlog |
| ATTACH-002 | Planned | security policy only | — | Backlog |
| ATTACH-003 | Planned | — | — | Backlog |

## Orders and inventory

| Requirement ID | Status | Relevant code/module | Tests or runtime evidence | Execution plan |
|---|---|---|---|---|
| ORDER-001 | Planned | — | — | Backlog |
| ORDER-002 | Planned | — | — | Backlog |
| ORDER-003 | Planned | — | — | Backlog |
| ORDER-004 | Planned | — | — | Backlog |
| INV-001 | Planned | — | — | Backlog |
| INV-002 | Planned | — | — | Backlog |
| INV-003 | Planned | — | — | Backlog |
| INV-004 | Planned | — | — | Backlog |
| INV-005 | Planned | — | — | Backlog |
| INV-006 | Planned | — | — | Backlog |
| INV-007 | Planned | — | — | Backlog |
| INV-008 | Planned | dashboard placeholders remain null | — | Backlog |

## Discovery and visualization

| Requirement ID | Status | Relevant code/module | Tests or runtime evidence | Execution plan |
|---|---|---|---|---|
| SEARCH-001 | In progress | global search page and core API search | PostgreSQL core search and Caddy global-search E2E; later catalogues absent | 002, Backlog |
| SEARCH-002 | In progress | registry search and pagination API | PostgreSQL oligo search; filters/sorting incomplete | 002 |
| SEARCH-003 | In progress | visible-query search base | permission unit tests; cross-scope search matrix incomplete | 002 |
| SEARCH-004 | In progress | exact duplicate conflict | PostgreSQL duplicate test; pre-submit suggestions incomplete | 002, Backlog |
| VIEW-001 | Planned | mapping service only | — | Backlog |
| VIEW-002 | Planned | — | — | Backlog |
| VIEW-003 | Planned | — | — | Backlog |
| VIEW-004 | Planned | strand-aware mapping data only | — | Backlog |
| VIEW-005 | Planned | assay expected amplicon field only | — | Backlog |
| VIEW-006 | Planned | mapping warnings service only | — | Backlog |

## Bioinformatics

| Requirement ID | Status | Relevant code/module | Tests or runtime evidence | Execution plan |
|---|---|---|---|---|
| BIO-001 | Verified | `target_mapping.py` | `test_target_mapping.py` forward/reverse/ambiguous cases | 001 |
| BIO-002 | Planned | TargetMapping design only | — | Backlog |
| BIO-003 | In progress | Primer3 worker tasks | 2 real Primer3 worker tests; API job persistence absent | 001, Backlog |
| BIO-004 | Verified | Wallace service, provenance, UI label | `test_sequence_analysis.py`; PostgreSQL response | 001, 002 |
| BIO-005 | Implemented | pinned BLAST+ worker image | image build/version check; governed databases blocked | 001, Backlog |
| BIO-006 | Planned | Celery infrastructure only | — | Backlog |
| BIO-007 | In progress | sequence/mapping error and warning states | sequence and mapping unit tests | 001, Backlog |

## Import, export, and audit

| Requirement ID | Status | Relevant code/module | Tests or runtime evidence | Execution plan |
|---|---|---|---|---|
| IMPORT-001 | Verified | `scripts/migration_excel`, migration report | checksum unchanged before/after preview | 001 |
| IMPORT-002 | Verified | preview/audit/normalization scripts | `test_excel_import.py`; 93/7 preview runtime | 001 |
| IMPORT-003 | Blocked | approval gate documented | Data-owner review not supplied | Backlog |
| IMPORT-004 | In progress | preview candidate decomposition/report | `test_excel_import.py`; write decomposition absent | 001, Backlog |
| IMPORT-005 | Planned | — | — | Backlog |
| EXPORT-001 | Planned | — | — | Backlog |
| EXPORT-002 | Planned | — | — | Backlog |
| EXPORT-003 | Planned | audit model only | — | Backlog |
| AUDIT-001 | In progress | `AuditEvent`, registry services | PostgreSQL create/update audit integration; later domains absent | 001, 002 |
| AUDIT-002 | In progress | safe audit helper and before/after snapshots | PostgreSQL update audit count; field assertions incomplete | 001, 002 |
| AUDIT-003 | Planned | — | — | Backlog |

## Deployment and continuity

| Requirement ID | Status | Relevant code/module | Tests or runtime evidence | Execution plan |
|---|---|---|---|---|
| DEPLOY-001 | Verified | `compose.yml`, pinned Dockerfiles | compose config and production image builds | 001 |
| DEPLOY-002 | Verified | Caddy and isolated networks | Compose health gates and live Playwright journey through Caddy | 001, 002 |
| DEPLOY-003 | Verified | status vocabulary and Playwright E2E | Build/API/browser evidence separated; Caddy E2E passed 2026-08-26 | 002 |
| BACKUP-001 | In progress | `infra/backup/create-backup.sh` | script/config only; no accepted backup runtime | 001, Backlog |
| BACKUP-002 | Planned | architecture documentation | — | Backlog |
| BACKUP-003 | In progress | `restore-test.sh`, runbook | no recorded successful production-like restore | 001, Backlog |
| BACKUP-004 | Blocked | documented pull topology | INRAE endpoint/ownership not supplied | Backlog |
| BACKUP-005 | Blocked | `SECURITY.md`, deployment/backlog docs | Institutional inputs absent | Backlog |

## Update discipline

Change this matrix in the same commit as any requirement status transition. A row
may become **Verified** only when its evidence column names a relevant automated
test or an explicit dated runtime validation. Browser-facing acceptance requires a
browser test through Caddy; API tests alone are insufficient.
