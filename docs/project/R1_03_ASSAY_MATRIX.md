# R1-03 — Assay integrity matrix

Scope: ASSAY-004, authorized editing, and existing ASSAY-006/007 version/lifecycle
behavior. Tests: `apps/api/tests/integration/test_assay_integrity.py` and permission
units. Each refusal compares independently reloaded database state before/after,
including assay version, references, contextual links and audit IDs.

| Rule / scenario | Create | Update | Persisted evidence |
|---|---|---|---|
| Duplicate oligo-role pair | 422 | 422 | No writes or audit |
| Role outside method allow-list | 422 | 422 | No writes or audit |
| Unknown role enum | 422 | 422 | No writes or audit |
| Missing, private inaccessible or foreign oligo | 422 | 422 | No writes or audit; no hidden name in error |
| Missing, private inaccessible or foreign target | 422 | 422 | No writes or audit; no hidden name in error |
| Missing/inactive experiment type | 422 | 422 | No writes or audit |
| Same oligo, two allowed contextual roles | Accepted | Preserved | Two association rows |
| Owner, project member/manager, foreign institute × four global roles | Existing create guards retained | Matrix checks 200/403/404 | Allowed deprecated/archive transitions persist version, stable ID, two links and audit; denied mutations unchanged |
| Viewer who owns or manages a project | Cannot create | 403 | Effective viewer role remains read-only |
| Identical metadata and associations | — | 200 | No version/audit increment |
| Replace contextual role/label and clear target | — | 200 | Exactly one replacement link, target null, version +1 and audit +1 |

## Demonstrated defects and corrections

- `can_edit` previously let ownership or contextual management bypass a global
  viewer role. The shared guard now rejects viewers before checking those grants.
  A unit regression and real PostgreSQL owner/manager cases reproduce the defect.
- An identical assay PATCH previously created an artificial version and audit.
  After authorization and reference validation, compare effective fields and the
  association set; return unchanged when there is no meaningful edit.
- The pre-existing registry integration test counted every update audit from all
  earlier tests. Restrict that assertion to its own actor to keep test isolation.

No schema change, new lifecycle policy, method metadata contract or hosting work.
Required metadata catalogue evolution remains outside ASSAY-004 in the existing
backlog. Existing Chromium assay creation/versioning and cross-project denial
scenarios provide browser regression coverage for this backend batch.
