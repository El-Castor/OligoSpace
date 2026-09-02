# Execution plan 004: Experiment runs, contextual validation, and attachments

- Status: completed
- Started: 2026-09-02
- Completed: 2026-09-02

## Objective

Make experimental evidence usable in the browser without changing reusable assay
definitions. Authorized users must record repeatable assay executions, append
contextual validation conclusions, and attach evidence whose provenance and safety
state remain explicit.

## Requirements in scope

- `EXPRUN-001` through `EXPRUN-003`.
- `VALID-001` through `VALID-004`.
- `ATTACH-001` through `ATTACH-003`.
- Evidence portions of `SEARCH-001`, `AUDIT-001`, and `AUDIT-002`.

Inventory-backed OligoLot relations remain outside this plan because the inventory
domain is not implemented. Run input metadata may record user-provided lot references,
but it MUST be labeled as contextual input and MUST NOT manufacture inventory records.
Malware scanning is an explicit publication gate: until a scanner marks an object
clean, browser and API responses MUST show it as quarantined and MUST NOT expose a
download/publication path.

## Existing capabilities to preserve

- Plans 001–003 browser-verified identity, workspaces, core registry, visibility,
  audit, Caddy ingress, and PostgreSQL persistence.
- Assays remain reusable/versioned definitions; runs and validations never mutate
  biological oligo identity or contextual assay-oligo roles.
- API authorization remains the security boundary; UI visibility is not access
  control.

## Data model and migrations

- Add `ExperimentRun` with stable public ID, assay and assay-version snapshot,
  operator, execution timestamp, project/team scope, protocol/version, conditions,
  contextual input/lot references, notes, status, visibility, and creator/updater.
- Add append-oriented `Validation` with stable public ID, assay, optional run,
  explicit result state, conclusion, measurements, validator/timestamp, notes, and
  optional superseded-validation link.
- Add `Attachment` metadata with stable public ID, exactly one run/validation parent,
  immutable object key, original filename, MIME type, byte size, SHA-256 checksum,
  uploader/timestamp, scan/publication state, and reversible removal/replacement
  provenance.
- Add a reversible Alembic revision with PostgreSQL constraints and indexes.

## Backend and authorization

- Provide list/create/detail/update APIs for runs; immutable execution provenance
  fields may not be silently rewritten.
- Provide list/create/detail APIs for validation evidence. Corrections append a new
  record that explicitly supersedes an accessible prior record.
- Validate that run/validation assay, project, team, and optional run context are
  mutually accessible and consistent.
- Accept bounded supported uploads, calculate checksum server-side, store the blob in
  private MinIO, and persist only metadata in PostgreSQL.
- Default every uploaded object to pending/quarantined. Removal is metadata/audit
  state and does not erase prior evidence or silently delete the object.
- Audit every create/update/supersession/upload/removal without storing file bodies.

## Frontend

- Replace planned Experiments and Validation pages with searchable list, create, and
  detail workflows.
- Link assay detail to its run history and to creation of a run or validation.
- Show assay version used, operator, timestamps, protocol, conditions, method-guided
  validation fields, supersession history, and attachment quarantine state.
- Keep all user-provided measurements and conclusions visibly labeled; do not infer a
  validation result from assay definition or oligo data.

## Tests

- Unit tests cover schema bounds, immutable/update rules, validation states, upload
  type/size policy, checksums, and parent constraints.
- PostgreSQL integration covers run repetition, assay-version snapshot, contextual
  validation, supersession, scope/authorization boundaries, attachment metadata,
  audit evidence, and persistence after transaction reload.
- Playwright through Caddy covers run create/detail, second run history, contextual
  validation, evidence upload/quarantine display, supersession, global search, and
  persistence after browser reload.
- Final host smoke remains required in addition to the internal Compose browser run.

## Completion criteria

- UI create → API → PostgreSQL → browser reload persistence passes for ExperimentRun,
  Validation, and attachment metadata.
- Multiple runs coexist without changing the assay definition or earlier evidence.
- Validation remains contextual and append-oriented; supersession retains the prior
  conclusion and files.
- Unsupported/oversized uploads are rejected and unscanned files remain quarantined.
- Required format, lint, typecheck, unit, PostgreSQL integration, Playwright through
  Caddy, production image build, Compose validation, and host-browser smoke pass.
- STATUS, BACKLOG, CHANGELOG, traceability, and this plan distinguish build, API, and
  browser evidence before the plan can move to `completed/`.

## Progress

- Activated after plan 003 passed build, API/PostgreSQL, six-spec Playwright-through-
  Caddy validation, and a separate host-network browser smoke test.
- Product requirements, data model, security boundary, architecture, scoped agent
  guides, existing migrations, core registry services, UI placeholders, and test
  conventions inspected before implementation.
- Added reversible migration `0003_experiment_evidence`, ExperimentRun, contextual
  append-oriented Validation, and Attachment metadata with PostgreSQL constraints,
  authorization, audit events, assay-version snapshots, and immutable provenance.
- Added private MinIO evidence storage. Supported bounded uploads are checksummed and
  remain pending/quarantined with no download path; removal retains metadata and the
  object. Malware scanning remains a later security integration, so `ATTACH-002`
  remains In progress rather than Verified.
- Replaced the Experiments and Validation placeholders with browser list/create/detail
  workflows, assay-linked run history, configurable validation guidance,
  supersession history, quarantine display, evidence-aware search, and a real
  dashboard count for runs awaiting a conclusion.
- Verified UI → API → PostgreSQL → browser reload persistence with 4 PostgreSQL
  integration tests and 7 Playwright specs through Caddy. The plan-004 browser spec
  covers two runs, real MinIO upload, contextual validation, supersession, search,
  dashboard rendering, and reload persistence.
- Passed format, Ruff, mypy, ESLint, TypeScript, 21 API unit tests, 2 worker tests,
  web tests, Compose validation, production runtime image builds, migration 0001 →
  0003, host ingress HTTP smoke, and the full Caddy browser suite.

## Outcome

The experiment evidence registry is usable in the development browser and plan 004
is complete. True relational OligoLot inputs remain dependent on the inventory plan;
malware scanning must be integrated before quarantined objects can ever be published
or downloaded.
