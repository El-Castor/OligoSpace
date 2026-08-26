# Product specification

## Product promise

OligoSpace helps a research team find, assess, reuse, validate, and physically
locate oligonucleotides and reusable assays without confusing a sequence with a
tube or a methodological category with an experiment execution.

## Primary workflows

1. Search before creating; reuse an existing biological sequence when appropriate.
2. Register a target and oligo with computed sequence QC and source provenance.
3. Define an assay using contextual roles such as forward, reverse, and probe.
4. Map assay oligos to a reference sequence and inspect ambiguity visually.
5. Record an experiment run and contextual validation without overwriting history.
6. Order a synthesis lot, register stock, move/consume it through immutable events.
7. Export or audit records with stable IDs and visible provenance.

## MVP boundary

The first milestone supplies the development stack, OIDC boundary, relational core,
basic registry API, dashboards/navigation, read-only Excel preview framework, and
scientific unit tests. Experiment runs, validation UI, inventory workflows, object
uploads, full-text search, mapping visualization, worker execution, and production
backup automation are subsequent phases and must not be represented as complete.

## Product principles

- Search and reuse beat silent duplication.
- Contextual validation beats global booleans.
- Actionable summaries beat decorative dashboards.
- User-entered, calculated, inferred, and experimentally validated facts are
  visibly distinct.
- Important scientific records are deprecated or versioned, not silently erased.

## How to read the requirements

The requirements below are the canonical functional catalogue, including planned
capabilities. Each stable ID has one acceptance statement. `MUST` is normative.
The relational representation is defined in `DATA_MODEL.md`, interaction details in
`UI_UX.md`, algorithms and reference handling in `BIOINFORMATICS.md`, and security
controls in `SECURITY.md`. Delivery evidence is maintained in
`REQUIREMENTS_TRACEABILITY.md`; implementation alone is not verification.

Institute visibility is represented by the current `organization` persistence
scope. User-facing language MUST say “Institute” while APIs may retain the stable
`organization` enum until a compatible migration is justified.

## Identity, access, and collaboration

- **AUTH-001 — Institutional authentication.** A user MUST authenticate through
  Keycloak OIDC Authorization Code with PKCE, without an OligoSpace password.
- **AUTH-002 — Development authentication.** A clearly marked local bypass MAY run
  only in development; production startup MUST reject it.
- **AUTH-003 — Server-side RBAC.** API authorization MUST enforce admin,
  team-manager, member, and viewer capabilities on every protected mutation.
- **AUTH-004 — Visibility.** Scientific records MUST support Private, Project,
  Team, and Institute visibility, and inaccessible records MUST not leak through
  lists, search, detail endpoints, counts, or identifiers.
- **AUTH-005 — Session security.** Tokens, issuer, audience, signature, expiry,
  secure-cookie, CORS, and disabled-account checks MUST follow `SECURITY.md`.

- **USER-001 — User profile.** A projected user MUST have an immutable OIDC subject,
  display name, email, active state, institute, and application role.
- **USER-002 — Account lifecycle.** Disabling a user MUST prevent new access while
  preserving authored records and audit history.
- **USER-003 — User dashboard.** An authenticated user MUST see actionable visible
  registry counts, recent work, validation work, and stock alerts without invented data.

- **TEAM-001 — Team management.** Authorized users MUST be able to create, describe,
  activate, and manage institute-scoped teams.
- **TEAM-002 — Team membership.** Admins/team managers MUST manage member roles, and
  those memberships MUST drive Team visibility and authorization.
- **TEAM-003 — Team dashboard.** A team view MUST summarize its projects, assays,
  validations, and inventory alerts using only records visible to the viewer.

- **PROJECT-001 — Project lifecycle.** Authorized users MUST create, describe,
  archive, and identify projects with stable public IDs.
- **PROJECT-002 — Project membership.** Project membership and role MUST be explicit
  and MUST govern Project visibility independently of UI control visibility.
- **PROJECT-003 — Project context.** Targets, oligos, assays, runs, validations, and
  inventory-relevant work MUST be linkable to a project where scientifically relevant.
- **PROJECT-004 — Project dashboard.** A project view MUST expose its reusable designs,
  experiment evidence, participants, and stock state without crossing visibility scopes.

## Scientific registry

- **ORGANISM-001 — Organism catalogue.** Admins MUST manage scientific name, optional
  common name, and taxonomy identifier without creating conflicting duplicates.
- **ORGANISM-002 — Organism reuse.** Targets, reference genomes, and assays MUST reuse
  catalogue organisms rather than copy free-text organism identity.

- **GENOME-001 — Reference genome identity.** A ReferenceGenome MUST identify organism,
  assembly name/version, source URIs, annotation format/version, and checksums.
- **GENOME-002 — Governed references.** Mapping and specificity results MUST name the
  exact immutable reference version/checksum used; missing references MUST remain explicit.
- **GENOME-003 — Reference ingestion.** Authorized ingestion MUST validate FASTA and
  supported annotation metadata before a reference can be selected for analysis.

- **TARGET-001 — Target registration.** A user MUST register a stable-ID target with
  type, organism/reference, gene/transcript identifiers, aliases, and description.
- **TARGET-002 — Known sequence only.** A reference sequence or coordinates MUST be
  stored only when supplied from a declared source; labels MUST never generate them.
- **TARGET-003 — Target lifecycle.** Authorized users MUST view, search, edit metadata,
  and deprecate/archive a target while preserving its public ID and audit history.
- **TARGET-004 — Target relationships.** A target MUST expose linked assays, mappings,
  transcripts, and evidence without claiming missing relationships.

- **OLIGO-001 — Oligo registration.** A user MUST register an oligo with stable public
  ID, name, type, sequence, ownership/visibility, description, and notes.
- **OLIGO-002 — Immutable biological identity.** Once created, an oligo sequence MUST
  not be edited; a different sequence MUST become a new oligo record.
- **OLIGO-003 — Normalization and validation.** Registration MUST remove whitespace,
  uppercase valid IUPAC bases, reject invalid/empty input, and preserve submitted evidence.
- **OLIGO-004 — Computed sequence QC.** Length, GC%, screening Tm, molecular weight,
  and reverse complement MUST be calculated where supported and labeled as computed.
- **OLIGO-005 — QC provenance.** Every computed value MUST retain algorithm/version,
  parameters or assumptions, timestamp, and unavailable/ambiguous state.
- **OLIGO-006 — Duplicate prevention.** Exact normalized duplicates within an institute
  MUST be rejected with the reusable public ID; reverse-complement matches MUST warn.
- **OLIGO-007 — Oligo lifecycle and reuse.** Visible oligos MUST be searchable,
  inspectable, metadata-editable, deprecatable/archivable, and linkable without deletion.

- **EXPTYPE-001 — Configurable catalogue.** Admins MUST manage ExperimentType name,
  slug, description, active state, allowed roles, required metadata, and validation hints.
- **EXPTYPE-002 — Method constraints.** Assay creation/update MUST reject contextual
  roles or required metadata that violate the selected active ExperimentType.
- **EXPTYPE-003 — Catalogue preservation.** Deactivating a type MUST prevent new use
  without invalidating historical assays that reference it.

- **ASSAY-001 — Assay registration.** A user MUST register a stable-ID assay with
  method, optional target/organism/project, expected product, protocol, and visibility.
- **ASSAY-002 — Contextual oligo roles.** AssayOligo MUST associate reusable oligos
  with explicit roles such as forward, reverse, probe, guide, donor, or adapter.
- **ASSAY-003 — Domain separation.** Direction and assay role MUST never be stored as
  intrinsic Oligo identity, and tube/lot facts MUST never be stored on AssayOligo.
- **ASSAY-004 — Association integrity.** An assay MUST reject inaccessible oligos,
  duplicate oligo-role pairs, invalid roles, and inaccessible targets.
- **ASSAY-005 — Expected amplicon.** PCR-like assays MAY declare expected product and
  amplicon length, which MUST remain distinct from computed mapping evidence.
- **ASSAY-006 — Versioned edits.** A meaningful assay edit MUST increment its version,
  retain before/after audit evidence, and preserve the stable public ID.
- **ASSAY-007 — Assay lifecycle.** Visible assays MUST be searchable, inspectable,
  reusable, editable by authorized users, and deprecatable/archivable.

## Experiment evidence and attachments

- **EXPRUN-001 — Experiment execution.** ExperimentRun MUST record an assay execution
  with date, operator, project, conditions, protocol/version, and optional lot usage.
- **EXPRUN-002 — Repeatable history.** Multiple runs MUST coexist without overwriting
  the reusable assay definition or previous evidence.
- **EXPRUN-003 — Run provenance.** Run metadata and attachments MUST identify who
  recorded them, when, and the assay version and inputs used.

- **VALID-001 — Contextual validation.** Validation MUST belong to an assay and
  optionally a specific run; it MUST never be a global boolean on an oligo.
- **VALID-002 — Validation states.** Status, conclusion, method-specific measurements,
  validator, timestamp, and notes MUST be explicit and preserve inconclusive evidence.
- **VALID-003 — Validation history.** New evidence MUST append or supersede explicitly;
  prior conclusions and supporting files MUST remain auditable.
- **VALID-004 — Method guidance.** Forms SHOULD use ExperimentType validation hints
  while retaining typed core facts and labeled dynamic metadata.

- **ATTACH-001 — Attachment metadata.** Authorized users MUST attach supported files
  to relevant records using object keys, content metadata, checksum, owner, and timestamp.
- **ATTACH-002 — Safe file handling.** Uploads MUST enforce size/type policy and a
  malware-scanning publication gate as specified in `SECURITY.md`.
- **ATTACH-003 — Evidence retention.** Removing or replacing an attachment MUST preserve
  its audit/evidence history according to retention policy.

## Suppliers, orders, and physical inventory

- **ORDER-001 — Supplier catalogue.** Authorized users MUST manage suppliers and
  catalogue/order references without conflating them with biological identity.
- **ORDER-002 — Purchase orders.** A PurchaseOrder MUST track supplier, requester,
  dates, institute/project context, external reference, status, and notes.
- **ORDER-003 — Order items.** Each OrderItem MUST link an oligo, synthesis options,
  quantity/scale, purification/modifications, price where allowed, and order status.
- **ORDER-004 — Receipt.** Receiving an order item MUST create or link an OligoLot and
  physical stock through explicit receipt events, never silent quantity mutation.

- **INV-001 — Oligo lots.** OligoLot MUST represent one synthesis batch with supplier,
  batch/order provenance, modifications, concentration/quantity metadata, and dates.
- **INV-002 — Stock items and aliquots.** StockItem/Aliquot MUST represent a physical
  container with stable ID, lot, quantity/unit, state, location, and optional barcode.
- **INV-003 — Hierarchical locations.** Locations MUST support institute-defined
  building/room/freezer/rack/box/position hierarchies and prevent conflicting siblings.
- **INV-004 — Occupancy integrity.** A physical position MUST not contain conflicting
  active stock placements, and moves MUST be transactional.
- **INV-005 — Immutable inventory events.** Receipt, aliquot, move, consume, adjust,
  reserve, release, loss, and disposal MUST append InventoryEvent records.
- **INV-006 — Quantity integrity.** Current stock MUST derive from or reconcile with
  events; negative or unit-incompatible changes MUST be rejected.
- **INV-007 — QR workflows.** Authorized users MUST generate and scan QR codes for
  stable stock/location identifiers and confirm the resolved record before mutation.
- **INV-008 — Stock alerts.** User/team dashboards MUST expose low, depleted, expired,
  misplaced, or reserved stock based on configurable thresholds and visible scope.

## Discovery and visualization

- **SEARCH-001 — Global search.** The persistent search entry MUST query visible public
  IDs, names, sequences, genes/transcripts, assays, projects, and inventory identifiers.
- **SEARCH-002 — Scoped registry search.** Registry lists MUST support deterministic
  filters, pagination, sorting, clear empty/error states, and reusable result links.
- **SEARCH-003 — No visibility leakage.** Result counts, suggestions, snippets, and
  exports MUST apply the same server-side visibility policy as detail endpoints.
- **SEARCH-004 — Reuse-first discovery.** Oligo and assay creation MUST expose exact or
  relevant existing matches before a duplicate design/order is committed.

- **VIEW-001 — GeneOligoViewer data integrity.** The viewer MUST render only persisted
  or freshly computed coordinates tied to a declared reference and provenance.
- **VIEW-002 — Transcript selection.** A user MUST select among known transcripts and
  see the selected accession/version; changing it MUST recompute the view explicitly.
- **VIEW-003 — Exon/intron structure.** Exons, introns, transcript direction, and
  genomic scale MUST be represented with a textual accessible fallback.
- **VIEW-004 — Oligo orientation.** Forward and reverse-complement hits MUST show strand,
  direction arrows, coordinates, role, and assay membership without relying on color.
- **VIEW-005 — Amplicon representation.** Compatible primer hits MAY show the expected
  amplicon span/length and MUST distinguish declared expectations from mapped results.
- **VIEW-006 — Ambiguity.** Multiple exact hits, incompatible orientation, missing
  transcript/reference, and unmapped oligos MUST produce explicit actionable warnings.

## Bioinformatics and scientific computation

- **BIO-001 — Exact target mapping.** The system MUST detect exact forward-strand and
  reverse-complement matches and return coordinates, strand, count, and ambiguity.
- **BIO-002 — Mapping persistence.** Persisted TargetMapping MUST retain algorithm,
  parameters, reference version/checksum, timestamp, match count, coordinates, and warnings.
- **BIO-003 — Primer3 QC.** Primer3 MUST provide configurable nearest-neighbor Tm,
  hairpin, homodimer, and pair-compatibility facts through reproducible worker jobs.
- **BIO-004 — Screening distinction.** Wallace Tm MUST remain labeled as a screening
  method and MUST never be presented as equivalent to configured Primer3 results.
- **BIO-005 — BLAST-ready specificity.** The architecture MUST support version-pinned
  BLAST databases/jobs/results without claiming specificity before governed references exist.
- **BIO-006 — Reproducible jobs.** Scientific jobs MUST persist tool/container version,
  inputs, parameters, reference IDs/checksums, state, timestamps, logs, and failure reason.
- **BIO-007 — Honest uncertainty.** Unsupported alphabets, ambiguous bases, multiple
  mappings, missing references, and failed jobs MUST yield explicit unavailable/warning states.

## Import, export, and audit

- **IMPORT-001 — Immutable source.** Excel audit/import MUST never modify the source
  workbook and MUST record its path, checksum, structure, and preview timestamp.
- **IMPORT-002 — Preview before write.** Import MUST produce deterministic proposed
  entities, normalized values, conflicts, warnings, and rejects before any database write.
- **IMPORT-003 — Reviewed write.** Database import MUST require explicit data-owner
  approval of mapping/conflict decisions and retain the approved preview evidence.
- **IMPORT-004 — Domain decomposition.** Import MUST separate Oligo, AssayOligo role,
  assay, order/lot, stock/location, validation, and placeholders without manufactured facts.
- **IMPORT-005 — Idempotency and lineage.** Re-running an approved import MUST avoid
  silent duplicates and link each created/updated record to source row and checksum.

- **EXPORT-001 — Registry export.** Authorized users MUST export visible selected data
  as XLSX, CSV, or TSV with stable IDs, timestamps, and provenance columns.
- **EXPORT-002 — Sequence export.** Oligos/targets MUST export as valid FASTA with
  stable identifiers and clear strand/sequence semantics.
- **EXPORT-003 — Export security.** Exports MUST enforce visibility, minimize sensitive
  fields, identify generator/time/filter, and create an audit event.

- **AUDIT-001 — Mutation audit.** Create, update, deprecate/archive, import, export,
  permission, validation, and inventory mutations MUST create append-oriented audit events.
- **AUDIT-002 — Audit evidence.** Events MUST record actor, time, action, entity,
  request correlation, and safe before/after facts without tokens, secrets, or file bodies.
- **AUDIT-003 — Audit access.** Authorized reviewers MUST search/export audit history;
  ordinary users MUST see relevant record history without gaining hidden-record access.

## Deployment, security, and continuity

- **DEPLOY-001 — Container deployment.** Version-pinned, non-root application containers
  MUST compose web, API, worker, PostgreSQL, Redis, Keycloak, MinIO, and Caddy services.
- **DEPLOY-002 — Public ingress.** Browser traffic MUST enter through Caddy; databases,
  cache, object/admin consoles, and internal service ports MUST remain private.
- **DEPLOY-003 — Runtime readiness.** Deployment acceptance MUST distinguish build,
  service runtime, and browser workflow verification; a successful build is insufficient.

- **BACKUP-001 — PostgreSQL-aware backup.** Backups MUST capture consistent database
  state, schema version, timestamps, checksums, retention metadata, and encryption policy.
- **BACKUP-002 — Object/reference coverage.** Recovery design MUST account for database,
  attachments, governed reference metadata/files, identity configuration, and secrets policy.
- **BACKUP-003 — Restore verification.** A backup MUST not be accepted until restored
  into an isolated target and smoke-tested with recorded outcome and duration.
- **BACKUP-004 — INRAE pull architecture.** The supported institutional design MUST
  permit INRAE-controlled pull replication/snapshots without inbound database exposure.
- **BACKUP-005 — Institutional inputs.** Production hostname, SSO/LDAP, backup endpoint,
  retention, encryption, and ownership decisions MUST remain Blocked—not guessed—until supplied.

## Verification states

- **Build verified:** static analysis and production artifacts succeed.
- **Service runtime verified:** migrations, health/readiness, API, and persistence run
  against the deployed PostgreSQL service.
- **Browser workflow verified:** an automated or explicit live browser journey passes
  through Caddy, including reload-based persistence checks.

The current state for every requirement is maintained in
`REQUIREMENTS_TRACEABILITY.md` and summarized in `project/STATUS.md`.
