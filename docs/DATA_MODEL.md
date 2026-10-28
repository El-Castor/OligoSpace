# Data model

All primary keys are UUIDs. User-facing records additionally use immutable public
identifiers allocated by the database/service (`OLG-000001`, `ASY-000001`, etc.).
Names remain editable and are never identifiers.

## Collaboration and visibility

`Organization` owns teams and institute-visible records. `User` projects an OIDC
subject. `TeamMembership` connects users to teams with admin, team-manager, member,
or viewer roles. `ProjectMembership` can narrow project access. Visibility values
are private, project, team, and organization. Resource ownership plus membership
is evaluated server-side; PostgreSQL row-level security is a production defense-in-
depth item after application policy has stable integration tests.

## Scientific registry

```text
Organization -> Team -> Project
Organism -> ReferenceGenome -> Target
ExperimentType -> Assay -> AssayOligo -> Oligo
                         -> Validation -> ExperimentRun
```

`Oligo` contains biological identity and a normalized sequence. Direction is not an
intrinsic oligo field. `AssayOligo.role` provides usage context. A target may point
to an organism/reference genome and contain a reference sequence for initial exact
mapping. A `TargetMapping` stores coordinates, strand, algorithm, parameters,
reference version, timestamp, match count, and warnings.

`ExperimentType` is administrator-managed. Its role and metadata requirements are
JSON documents because they are catalog configuration, not core relationships.
`Validation` belongs to an assay and optionally a run; status is contextual.

## Persistent scientific jobs

```text
Oligo ────────────────> ScientificJob ──> ScientificJobAttempt (append-oriented)
Assay + Forward/Reverse ─────┘       └──> ScientificJobResult (immutable, one-to-one)
```

`ScientificJob` is the durable request envelope and lifecycle authority. It stores a
stable `SJOB` public ID, requester and derived visibility scope, exactly one valid
subject shape, immutable input snapshot/digest, requested and effective parameters,
schema versions, execution fingerprint, claim token, state, retry budget, and UTC
timestamps. A partial unique index prevents concurrent active duplicates for one
requester and effective request; idempotency keys are requester/institute scoped.

Each claim appends a numbered `ScientificJobAttempt` with task/claim identity, lease,
worker/tool/build provenance and bounded safe error facts. A successful job owns one
immutable `ScientificJobResult` with typed component payload, units, warnings,
Primer3 version/source checksum, wrapper/worker/build identity and execution times.
Foreign keys use restrictive deletion so scientific evidence cannot be orphaned.
Reads re-evaluate current access to the source Oligo or Assay in addition to the
immutable visibility snapshot.

## Physical inventory

```text
Supplier -> PurchaseOrder -> OrderItem -> Oligo
Oligo -> OligoLot -> StockItem -> Location
                         |          -> InventoryEvent (append-only)
                         -> modifications
```

Locations form an adjacency-list hierarchy so buildings, rooms, freezers, boxes,
and positions are configurable. A unique parent/name/type constraint prevents
duplicate siblings; occupied-position rules are transactional. Quantity changes
must create inventory events. Biological and order statuses use separate enums.

## Cross-cutting records

`AuditEvent` is append-oriented. `Attachment` stores object keys and content
metadata, never the blob. Soft-deletable scientific entities carry status or
`deprecated_at`; destructive deletion is restricted. JSONB is limited to dynamic
metadata, audit snapshots, mapping parameters, and experimental conditions.
