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
| AUTH-001 | Implemented | `apps/web/lib/auth.ts`, NextAuth route, Keycloak realm | Development login E2E; institutional OIDC browser flow not exercised | 001, 003 |
| AUTH-002 | Verified | signed development session, production runtime guard | `test_auth.py`; auth/logout/second-identity Caddy E2E | 003 |
| AUTH-003 | Verified | `domain/permissions.py`, registry/workspace services | permission units; PostgreSQL admin/member 403 integration; admin-denial E2E | 001, 002, 003 |
| AUTH-004 | In progress | visibility queries and scope validation across registry/workspaces; visibility-filtered reuse hints | Plan 006 four-scope/four-role core registry matrix, membership revocation and cross-project E2E; export not implemented | 001, 002, 003, 006 |
| AUTH-005 | In progress | `security/auth.py`, token refresh, secure cookies, CORS, Caddy headers | disabled-account PostgreSQL test and development session E2E; production OIDC absent | 001, 003 |
| USER-001 | Verified | expanded User model, `/me`, profile API/page | PostgreSQL profile test; profile save/reload Caddy E2E | 001, 003 |
| USER-002 | In progress | inactive-user rejection and preserved relational authorship | disabled-account PostgreSQL test; authored-history lifecycle not yet explicit | 003 |
| USER-003 | In progress | personalized dashboard service/page | dashboard Caddy E2E; later validation/stock actions explicitly unavailable | 001, 003 |
| TEAM-001 | In progress | workspace Team CRUD API and admin/team pages | PostgreSQL create and detail tests; activation browser path untested | 003 |
| TEAM-002 | Verified | TeamMembership CRUD, role-aware principal, visibility policy | permission units; PostgreSQL membership/403/visibility; Team Caddy E2E | 001, 003 |
| TEAM-003 | In progress | Team detail dashboard and visible resource counts | Caddy Team/project view; validation/inventory summaries unavailable | 003 |
| PROJECT-001 | In progress | Project CRUD, stable IDs, status, visibility, migration `0002` | PostgreSQL create; Caddy create/detail/reload; archive path untested | 003 |
| PROJECT-002 | Verified | ProjectMembership CRUD and server permission policy | PostgreSQL membership/visibility/403; membership and denial Caddy E2E | 001, 003 |
| PROJECT-003 | In progress | project links on Targets/Oligos/Assays and scope-aware forms | core form build/E2E plus Project linked-resource view; later domains absent | 001, 002, 003 |
| PROJECT-004 | In progress | Project detail dashboard, participants, linked resources, counts | Project create/membership/reload Caddy E2E; evidence/stock states unavailable | 003 |

## Scientific registry

| Requirement ID | Status | Relevant code/module | Tests or runtime evidence | Execution plan |
|---|---|---|---|---|
| ORGANISM-001 | Implemented | organism model, admin list/create/update routes and controls | Static/type/build validation; no catalogue mutation E2E | 001, 003 |
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
| EXPTYPE-001 | Implemented | model, seed, admin create/update routes and controls | seed/runtime plus static/type/build validation; no mutation E2E | 001, 003 |
| EXPTYPE-002 | In progress | assay role validation | PostgreSQL valid-role integration; required metadata not enforced | 001, 002 |
| EXPTYPE-003 | Implemented | active filter, admin active-state control, restrictive assay FK | Migration/schema and build validation; deactivation behavior test incomplete | 001, 003 |
| ASSAY-001 | Verified | assay create/search/detail/edit API and pages | PostgreSQL route integration; Caddy create/detail/reload E2E | 001, 002 |
| ASSAY-002 | Verified | `AssayOligo`, contextual-role form | PostgreSQL association integration; Forward/Reverse Caddy E2E | 001, 002 |
| ASSAY-003 | Implemented | separate Oligo/AssayOligo/Assay models | ADR-0004 and schema validation | 001 |
| ASSAY-004 | Verified | `_validate_assay_references` | R1-03 create/update negative matrix; independent-session no-side-effect checks; positive two-role/replacement cases; `docs/project/R1_03_ASSAY_MATRIX.md` | 001, 002, 006 |
| ASSAY-005 | Verified | expected product/amplicon API and UI | Expected amplicon asserted by Caddy E2E | 002 |
| ASSAY-006 | Verified | version increment and before/after audit | PostgreSQL version/audit integration | 002 |
| ASSAY-007 | In progress | search/detail/edit/status workflows | PostgreSQL API and Caddy edit/version/reload E2E; archive path untested | 002 |

## Experiment evidence and attachments

| Requirement ID | Status | Relevant code/module | Tests or runtime evidence | Execution plan |
|---|---|---|---|---|
| EXPRUN-001 | In progress | `models/laboratory.py`, laboratory API/UI; true OligoLot relation awaits inventory | PostgreSQL laboratory integration and experiment-evidence Caddy E2E | 004, Backlog |
| EXPRUN-002 | Verified | repeated run API/UI with Assay version snapshot | PostgreSQL laboratory integration and experiment-evidence Caddy E2E | 004 |
| EXPRUN-003 | Verified | immutable run provenance, contextual inputs, attachments | API units, PostgreSQL laboratory integration, experiment-evidence Caddy E2E | 004 |
| VALID-001 | Verified | separate append-oriented `Validation` model/API/UI | PostgreSQL laboratory integration and experiment-evidence Caddy E2E | 004 |
| VALID-002 | Verified | assay-level or run-context validation with user-entered evidence | API units, PostgreSQL laboratory integration, experiment-evidence Caddy E2E | 004 |
| VALID-003 | Verified | explicit supersession preserving prior evidence | PostgreSQL laboratory integration and experiment-evidence Caddy E2E | 004 |
| VALID-004 | Verified | `ValidationForm` renders ExperimentType measurement guidance | experiment-evidence Caddy E2E | 004 |
| ATTACH-001 | Verified | private MinIO upload plus PostgreSQL checksum/provenance metadata | PostgreSQL laboratory integration and real-MinIO Caddy E2E | 004 |
| ATTACH-002 | In progress | size/type policy and mandatory pending/quarantine gate; malware scanner absent | API units, PostgreSQL rejection tests, quarantine Caddy E2E | 004, Backlog |
| ATTACH-003 | Verified | soft removal retains metadata/object and audit history | PostgreSQL laboratory integration | 004 |

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
| SEARCH-001 | In progress | global search page/API for core registry, Projects, runs, and validations | PostgreSQL core/evidence search and Caddy global-search E2E; inventory absent | 002, 003, 004, Backlog |
| SEARCH-002 | In progress | registry search and pagination API | PostgreSQL oligo search; filters/sorting incomplete | 002 |
| SEARCH-003 | In progress | visible-query registry and workspace searches; duplicate/reverse hints respect current visibility | Plan 006 core list/detail/search/counts/choices matrix and cross-project E2E; exports absent | 002, 003, 006 |
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
| BIO-003 | Verified | persistent scientific API/worker and Oligo/Assay UI | `test_scientific_contract.py` real Primer3 fixtures; API and PostgreSQL tests; Caddy E2E `apps/web/e2e/scientific-jobs.spec.ts`; `docs/project/PLAN_005_RECOVERY_EVIDENCE.md` | 001, 005 |
| BIO-004 | Verified | Wallace service, provenance, UI label | `test_sequence_analysis.py`; PostgreSQL response | 001, 002 |
| BIO-005 | Implemented | pinned BLAST+ worker image | image build/version check; governed databases blocked | 001, Backlog |
| BIO-006 | In progress | `ScientificJob`/attempt/result, migration 0004, Celery worker/Beat | reversible PostgreSQL migration and API integration; worker kill, Redis restart and stuck-job reconciliation on `oligospace-e2e` (`docs/project/PLAN_005_RECOVERY_EVIDENCE.md`, scenarios A/B1/B2/C); `test_attempt_fencing.py` | 005 |
| BIO-007 | Verified | explicit scientific validation/error states and neutral UI | API boundary tests and worker timeout/output/version tests; Caddy E2E `scientific-jobs.spec.ts` "Primer3 rejects ambiguous DNA without creating a scientific result" | 001, 005 |

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
| AUDIT-001 | In progress | `AuditEvent`, API insertion boundary and mutation services | R1-05 persisted core/workspace/evidence/job matrix; later import/export/inventory mutations absent | 001, 002, 003, 006 |
| AUDIT-002 | In progress | request correlation, recursive structured-fact redaction, safe before/after snapshots | R1-05 actor/time/action/entity/correlation and no-file-body/no-header checks; nested credentials, concurrent requests and revoked-activity regression; async worker events retain job/attempt correlation | 001, 002, 003, 006 |
| AUDIT-003 | Planned | — | — | Backlog |

## Deployment and continuity

| Requirement ID | Status | Relevant code/module | Tests or runtime evidence | Execution plan |
|---|---|---|---|---|
| DEPLOY-001 | Verified | `compose.yml`, pinned Dockerfiles | compose config and production image builds | 001 |
| DEPLOY-002 | Verified | Caddy, isolated networks, E2E Caddy network namespace | Compose health gates, 6 Caddy specs, host-network smoke on 2026-09-02 | 001, 002, 003 |
| DEPLOY-003 | Verified | status vocabulary, split Playwright E2E, host smoke | Build/API/browser evidence separated; Caddy and host-network smoke passed 2026-09-02 | 002, 003 |
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
