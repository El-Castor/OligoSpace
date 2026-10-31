# R1-05 — Audit coverage and disclosure prevention

Scope: currently implemented MVP API mutations (AUDIT-001/002). Future import writes,
exports and inventory need their own audit cases when those features exist; this
batch does not claim those requirements are complete globally.

| Surface | Test / evidence |
|---|---|
| Oligo, Target, Assay create/update/deprecate/archive | 12 parameterized PostgreSQL cases |
| ExperimentType and Organism create/update | 4 PostgreSQL cases |
| User create/admin-update/profile-update | 3 PostgreSQL cases |
| Team create/update and member add/change/remove | 5 PostgreSQL cases |
| Project create/update/deprecate/archive and member add/change/remove | 7 PostgreSQL cases |
| ExperimentRun create/update, Validation create/supersede, attachment upload/remove | 6 PostgreSQL cases, including two events for supersession |
| Scientific submit and retry | Existing job integration extended with independent-session retry event/state/correlation assertions |
| HTTP correlation | Unit tests for missing/invalid/oversize headers, concurrent isolation and ContextVar reset |
| Structured sensitive facts | Nested PostgreSQL and recursive unit tests; tokens, passwords, secrets, API keys, private keys, credentials and file-body keys redacted |
| Revoked record activity | Former project manager no longer receives the hidden Assay UUID in the dashboard |

Each mutation case reloads audit rows through an independent database session and
asserts actor, timestamp, action, entity and request ID, exact new-event cardinality,
and unchanged prior events. Request Authorization/Cookie headers and uploaded file
bodies must not appear in audit facts. Lifecycle and rejected-operation persistence
are also protected by R1-03. Browser regression remains the existing Chromium suite.

## Corrected defects

1. API events had no request correlation despite the existing nullable request_id
   column. Middleware now validates or generates an ID, returns it in X-Request-ID,
   and isolates context per request. API ORM inserts inherit that context.
2. Arbitrary nested assay method metadata copied structured credentials/file bodies
   into audit snapshots. A single API AuditEvent insert boundary now copies and
   redacts recognized sensitive keys recursively. Review added private-key and
   credential aliases; those failures were reproduced before extending the filter.
3. Own-actor recent activity ignored current record visibility after permission
   revocation. The dashboard now applies existing resource visibility queries before
   ordering/limiting events and fails closed for unknown entity types.

No existing audit history is rewritten. API correlation does not manufacture an
HTTP request for asynchronous worker events: those retain job/attempt correlation.
The key filter is defense in depth, not a detector of secrets embedded in arbitrary
prose. Callers must still select safe facts; no request headers or raw file bodies
are copied. Audit review/export UI and database-enforced immutability remain outside
this batch. No schema migration, host action or deployment.
