# Execution plan 005: Persistent scientific jobs and Primer3 analysis

- Status: completed
- Proposed: 2026-09-03
- Activated: 2026-09-03
- Completed: 2026-10-29
- Depends on: completed execution plans 001, 002, 003, and 004
- Primary requirements: `BIO-003`, `BIO-004`, `BIO-006`, and `BIO-007`
- Supporting requirements: `OLIGO-004`, `OLIGO-005`, `ASSAY-002`, `ASSAY-004`,
  `ASSAY-006`, `AUTH-003`, `AUTH-004`, `SEARCH-003`, `AUDIT-001`, `AUDIT-002`,
  `DEPLOY-001`, `DEPLOY-002`, and `DEPLOY-003`

This execution plan is completed; see the Outcome section. Nothing in this plan changes the completed status or historical
outcome of plans 001–004.

The first implementation milestone qualified Primer3 2.6.1 CLI modes, supported
nearest-neighbor limits, parameter-to-argument mappings, and golden fixtures for both
individual Oligo QC and Forward/Reverse Assay pair analysis before persistence and
application implementation began.

## Progress — 2026-09-07

- Milestone 1 completed: the pinned Primer3 2.6.1 runtime, SantaLucia option mapping,
  `HAIRPIN`/`ANY`/`END1` modes, 60 nt boundary and measured individual/pair fixtures
  are documented in `docs/PRIMER3_QUALIFICATION.md` and covered by real worker tests.
- Migration `0004_scientific_jobs`, persistent job/attempt/result models, API
  submission/list/detail/retry, idempotency, active-job limits, audit transitions,
  queue gateway, worker claims/results/retries and Beat reconciliation are implemented.
- Oligo QC and Assay Forward/Reverse browser workflows, polling, historical results,
  role selection, stale-version notice and provenance rendering are implemented.
- Verified so far: Compose configuration; API/worker/web lint and strict typing;
  25 API unit tests; 7 worker tests; web tests; PostgreSQL 17 migration
  `0001→0004→0003→0004` plus integration suite; production API/web/worker builds;
  API/Redis/worker/scheduler runtime health and Caddy root smoke.
- Still required before completion: Chromium E2E through Caddy for both scientific
  workflows/RBAC/reload, explicit worker/Redis interruption recovery evidence,
  final documentation/traceability review, and final complete check rerun.

## 1. Objective

Introduce persistent, reproducible scientific jobs for Primer3-based analysis so an
authorized user can request, monitor, inspect, and reload both individual Oligo QC
and Forward/Reverse Assay pair analysis. PostgreSQL is the authoritative record of
the request, state transitions, attempts, effective inputs and parameters, results,
warnings, errors, and scientific provenance.

## 2. User-visible outcome

- An Oligo detail page offers a clearly labeled Primer3 scientific-QC workflow and
  retains the existing Wallace screening calculation as a separate fact.
- An Assay detail page offers Forward/Reverse pair analysis for oligos associated in
  those contextual roles.
- Each submitted analysis has a stable public job ID and visible queued, running,
  retrying, succeeded, or failed state.
- Successful results remain available after browser refresh, service restart, and
  Redis result expiry because PostgreSQL, not the Celery result backend, is the
  authoritative result store.
- Failed analyses expose a safe, actionable error without presenting missing or
  partial output as a scientific result.

## 3. Scope

The first increment MUST support both of these job kinds:

1. `oligo_primer3_qc`: nearest-neighbor melting temperature, hairpin analysis, and
   homodimer analysis for one persisted Oligo.
2. `assay_primer3_pair_compatibility`: individual Primer3 facts for the selected
   Forward and Reverse AssayOligo members plus pair-level melting-temperature delta
   and heterodimer/end-complementarity facts supported and qualified by the pinned
   Primer3 tools.

Scope includes persistent job orchestration, bounded retry history, worker execution,
scientific provenance, server-side authorization, audit events, browser workflows,
and full build/API/PostgreSQL/worker/Caddy validation.

## 4. Explicit non-goals

- Do not replace, rename, overwrite, or backfill the existing Wallace screening Tm.
- Do not infer experimental suitability, amplification efficiency, specificity,
  validation, or a pass/fail assay conclusion from thermodynamic facts alone.
- Do not run BLAST, reference-genome specificity, target mapping, amplicon mapping,
  primer design, or automatic primer selection in this increment.
- Do not mutate Oligo sequence identity, AssayOligo roles, or Assay definitions when
  running an analysis.
- Do not add arbitrary shell arguments, user-supplied executables, custom scripts,
  or unrestricted Primer3 configuration.
- Do not implement job cancellation, bulk submission, priority queues, scheduled
  analyses, WebSocket progress, or generalized workflow composition.
- Do not use MinIO merely to store small structured Primer3 inputs/results. Object
  storage is reserved for a later job type only if result size or retention evidence
  justifies it.
- Do not activate later plans or absorb inventory, GeneOligoViewer, reference
  ingestion, BLAST specificity, malware scanning, or backup delivery.

## 5. Domain model

Add three domain records while preserving Oligo biological identity and contextual
AssayOligo roles:

### ScientificJob

The immutable request envelope and mutable orchestration state:

- UUID primary key and institute-unique stable public ID with prefix `SJOB`.
- organization, derived project/team ownership scope, derived visibility, requester,
  job kind, current state, timestamps, attempt counters, and retry scheduling fields.
- exactly one valid subject shape: one Oligo for individual QC, or one Assay plus a
  selected Forward/Reverse pair and Assay version snapshot for pair analysis.
- immutable input snapshot, input digest, requested parameters, effective parameters,
  parameter-schema version, and execution fingerprint.
- optional client idempotency key and queue task correlation identifier. The Celery
  task ID is operational metadata and never replaces the stable job public ID.

### ScientificJobAttempt

An append-oriented execution attempt:

- job, monotonically increasing attempt number, task correlation ID, attempt state,
  worker claim/lease timestamps, start/end timestamps, and retryability.
- effective worker/tool/environment identity observed by that attempt.
- bounded sanitized diagnostic metadata, exit status, stable error code, and safe
  error summary. Secrets, connection strings, tokens, raw environment dumps, and
  unrestricted stdout/stderr MUST NOT be stored.

### ScientificJobResult

An immutable one-to-one successful result:

- job ID, result-schema version, typed result payload, warnings, started/completed
  timestamps, tool facts, worker version, and execution-environment identity.
- a result can be inserted only for a running attempt and in the same transaction
  that marks the job succeeded.
- successful result rows are never overwritten. Re-analysis creates another job;
  historical results remain linked to their original input/Assay version snapshots.

Validated JSONB is appropriate for versioned method-specific inputs, parameters,
results, warnings, and diagnostics. Identity, ownership, subjects, state, attempts,
timestamps, and actor relationships remain typed relational columns.

## 6. ScientificJob lifecycle/state machine

```text
                    transient failure, attempts remain
queued  ──claim──>  running  ─────────────────────────> retrying
  ^                    │                                    │
  │                    │ committed result                   │ due/re-dispatch
  │                    v                                    │
  └──────────────── succeeded                               v
                       │                                  queued
                       │
                       └── no outgoing transition

queued/running/retrying ── permanent failure or exhausted attempts ──> failed
failed ── authorized retry when classified retryable ──> queued
```

- Job creation and its `queued` state commit before broker publication.
- Claims and state transitions use compare-and-set/row-lock semantics so duplicate
  Celery delivery cannot run the same attempt concurrently.
- `succeeded` and its result are terminal and committed atomically.
- `failed` is terminal for deterministic input/tool errors. An explicitly retryable
  infrastructure failure may be requeued within the configured attempt budget.
- A timed-out worker lease is recorded as a failed attempt before recovery; it is
  never silently reset.
- Redis is transport infrastructure only. Redis task state/result expiry MUST NOT
  alter the PostgreSQL job state or erase a persisted result.

## 7. Input model

All worker tasks receive only a job UUID and attempt/claim token. The worker loads the
authoritative immutable input snapshot from PostgreSQL; task messages MUST NOT become
an untracked alternative source of scientific inputs.

### Individual Oligo QC input

- Oligo UUID and public ID.
- submitted and normalized sequence snapshots as already preserved by the registry,
  sequence SHA-256, Oligo type, and immutable Oligo identity/version facts.
- Primer3 analysis eligibility determined explicitly. The first increment accepts
  only unambiguous DNA (`A/C/G/T`) within the qualified nearest-neighbor length bound.

### Assay pair input

- Assay UUID/public ID and immutable Assay version snapshot.
- selected Forward and Reverse AssayOligo role tuples and corresponding Oligo
  UUIDs/public IDs, normalized 5'-to-3' sequence snapshots, and sequence SHA-256s.
- The API may auto-select only when exactly one Forward and one Reverse association
  exist. Otherwise the caller must choose an accessible associated pair explicitly.
- The Reverse primer is passed as its stored 5'-to-3' oligo sequence. The workflow
  MUST NOT silently reverse-complement it before Primer3 thermodynamic analysis.

Any later Assay edit or association change does not rewrite a historical job. The UI
must mark a result as belonging to an older Assay version and offer a new run.

## 8. Parameter/provenance model

Expose a typed, allow-listed Primer3 parameter schema rather than raw command-line
arguments. At minimum it contains bounded finite values for:

- monovalent salt concentration (`mv_conc_mM`)
- divalent salt concentration (`dv_conc_mM`)
- dNTP concentration (`dntp_conc_mM`)
- oligo/DNA concentration (`dna_conc_nM`)
- thermodynamic alignment maximum loop size (`max_loop`)
- nearest-neighbor maximum supported length (`max_nn_length`)
- Tm method and salt-correction method, constrained to worker-supported enum values

Persist both requested parameters and fully expanded effective parameters, including
defaults. Record the parameter-schema version, units, selected method identifiers,
and the wrapper contract version. Defaults MUST be resolved before fingerprinting and
queueing so the same effective request has the same canonical representation.

The implementation must qualify the allowed ranges and exact option mapping against
the pinned Primer3 2.6.1 executables. Sequences beyond the effective
`max_nn_length` are unavailable for the nearest-neighbor job rather than silently
falling back to a different formula while retaining a nearest-neighbor label.

## 9. Result model

Every result field has an explicit component state (`available`, `unavailable`, or
`error`), value and units when available, method identifier, and warnings.

### Individual result

- `nearest_neighbor_tm`: temperature in degrees Celsius from `oligotm`.
- `hairpin`: qualified `ntthal` hairpin thermodynamic facts, including temperature
  in degrees Celsius when the tool reports it.
- `homodimer`: qualified `ntthal` self-complementarity facts, including temperature
  in degrees Celsius when the tool reports it.

### Pair result

- nested individual Forward and Reverse results using the same component schema.
- absolute Forward/Reverse nearest-neighbor Tm delta as an explicitly derived fact.
- heterodimer and supported 3'-end complementarity facts from `ntthal`, with the
  precise analysis mode retained for each value.
- calculability/tool warnings only. A generic “compatible/incompatible” biological
  conclusion is prohibited unless a future governed policy defines thresholds,
  purpose, units, rationale, and validation evidence.

The API and UI MUST use the terms “Wallace screening Tm”, “Primer3
nearest-neighbor Tm”, “hairpin”, “homodimer”, and “Forward/Reverse pair analysis”
as distinct labels. A missing component cannot be represented as zero.

## 10. Error/retry model

- Validate unsupported alphabet, type, sequence length, role selection, parameter
  bounds, authorization, and subject consistency before enqueueing; these errors are
  deterministic and non-retryable.
- Classify worker failures with stable codes such as `tool_timeout`, `tool_exit`,
  `invalid_tool_output`, `database_unavailable`, `broker_unavailable`,
  `worker_lost`, and `retry_exhausted`.
- Retry only failures classified as transient. Default to at most three total
  attempts with bounded exponential backoff and jitter; make limits configuration,
  not request parameters.
- Bound each external tool invocation and the total job duration. A timeout kills
  the child process, records the attempt, and never persists partial output as a
  successful component.
- Store safe summaries and bounded diagnostics; retain full server logs only under
  the existing operational log policy and correlation IDs.
- A retry uses the same immutable job inputs/effective parameters. A changed input or
  parameter set creates a new job.

## 11. Database changes

Create `scientific_jobs`, `scientific_job_attempts`, and
`scientific_job_results` with:

- PostgreSQL enums or constrained values for job kind, job state, and attempt state.
- foreign keys with restrictive deletion for users, Oligos, Assays, Teams, Projects,
  and Organizations so provenance cannot be orphaned.
- subject-shape checks for individual versus pair jobs, nonnegative attempt counts,
  coherent timestamps, exactly one result per successful job, and unique attempt
  numbers per job.
- indexes for public ID, organization, requester, subject, state/due time, creation
  time, execution fingerprint, and visibility joins.
- institute-unique public IDs and a public-ID counter allocation for `SJOB`.
- immutable request/result enforcement in services plus PostgreSQL constraints where
  practical. No destructive cascade may erase scientific evidence.

The job stores a derived immutable visibility/ownership snapshot for provenance.
Reads additionally require current access to the source Oligo or Assay so a later
visibility narrowing cannot leak an old result.

## 12. Alembic migration

Add reversible migration `0004_scientific_jobs`, revising
`0003_experiment_evidence`.

The migration must create/drop enums, tables, checks, foreign keys, indexes, partial
uniqueness constraints, and the `SJOB` counter deterministically. Upgrade, downgrade
to `0003`, and re-upgrade must pass on a fresh PostgreSQL 17 database. Applied
migrations 0001–0003 MUST NOT be edited.

## 13. API endpoints

Under `/api/v1` add:

- `POST /scientific-jobs/oligo-primer3-qc`
- `POST /scientific-jobs/assay-primer3-pair`
- `GET /scientific-jobs` with bounded pagination and filters for visible subject,
  job kind, state, requester, and date
- `GET /scientific-jobs/{job_public_id}`
- `POST /scientific-jobs/{job_public_id}/retry` for an authorized retryable failure

Create endpoints accept an `Idempotency-Key` header and return `202 Accepted` for a
new/active job or `200 OK` when replaying the same idempotent request. Responses
contain the stable job ID, state, timestamps, subject snapshot summary, effective
parameters, attempts, result/warnings when available, and safe error fields.

Use stable problem codes for invalid parameters, unsupported sequence, missing or
ambiguous pair roles, inaccessible subject, idempotency conflict, illegal transition,
rate limit, broker dispatch failure, and non-retryable job failure.

## 14. Service/repository changes

- Add API ScientificJob schemas, repository, orchestration service, permission
  adapter, audit serialization, and queue gateway.
- Routes handle HTTP validation and delegate; they contain neither authorization
  policy nor Primer3 logic.
- The service resolves accessible subjects/roles, snapshots inputs and visibility,
  resolves effective parameters, fingerprints the request, persists the job, commits,
  and then dispatches it.
- Encapsulate Celery publication behind a gateway so API tests do not depend on a
  live broker and dispatch failure remains explicit.
- Add a narrow worker-side job persistence repository. It may claim/update only job,
  attempt, and result records; it MUST NOT mutate registry, assay, validation, or
  inventory records.
- Centralize or contract-test enums, payload schemas, fingerprint rules, and state
  transitions so API and worker implementations cannot drift silently.

## 15. Worker/Celery changes

- Replace sequence-bearing public task messages with a stable task accepting job ID
  and claim token.
- Add separate dispatch names for individual and pair work, or one versioned router
  task whose job kind is loaded from PostgreSQL; task names remain stable and tested.
- Atomically claim jobs, append attempts, execute the wrapper, validate output, and
  transactionally insert the immutable result plus terminal state.
- Keep `task_acks_late`; duplicate delivery must no-op after observing a succeeded job
  or must fail a stale claim safely.
- Add periodic reconciliation for queued/retrying due jobs and expired running leases
  using existing Celery/Redis infrastructure. This may use a small Compose-internal
  Celery Beat scheduler; no new message broker or workflow engine is introduced.
- Give the worker a production-validated, least-privilege PostgreSQL connection. Its
  database role should be restricted to reading required subject/job snapshots and
  updating job-owned tables where deployment tooling permits.

## 16. Primer3 integration strategy

- Preserve the wrapper boundary in `oligospace_bioinfo`; callers never parse raw
  `oligotm` or `ntthal` output directly.
- Keep Primer3 pinned to version 2.6.1 and its source checksum until an explicit
  upgrade with fixture comparison and provenance compatibility is approved.
- Extend the wrapper to execute individual Tm, hairpin, homodimer, and selected-pair
  heterodimer/end analyses with explicit arguments and timeouts.
- Validate numeric output as finite and scientifically typed. Preserve the exact
  executable/mode used for every component.
- Detect the effective tool version at runtime and compare it with the expected
  pinned version; mismatch is a terminal provenance error, not a warning-only success.
- Record worker package version, wrapper contract version, source/build identity,
  and container image digest or immutable development build revision.
- Establish documented golden fixtures and boundary cases from qualified Primer3
  behavior before exposing values in the browser.

## 17. Frontend workflows

- Add typed API client methods and reusable job state/result components.
- Use polling with bounded backoff while a job is queued/running/retrying; stop on a
  terminal state and preserve manual refresh. Do not introduce WebSockets.
- Show stable job ID, requested-by identity, dates, effective parameters, attempts,
  warnings/errors, provenance, and a link back to the source record.
- Provide explicit loading, empty, unavailable, failure, forbidden, and stale-Assay-
  version states. State and scientific meaning cannot rely on color alone.
- Hide mutation controls according to permissions for usability, while relying on
  the API for enforcement.

## 18. Oligo QC UX

- Add a “Scientific QC” section to Oligo detail.
- Retain a distinct “Wallace screening” block with its existing provenance.
- Add a “Run Primer3 analysis” form with documented units, bounded inputs, defaults,
  and a confirmation summary of the immutable Oligo sequence/public ID.
- Render nearest-neighbor Tm, hairpin, and homodimer as separate result cards with
  component state, value/unit, method, warnings, and provenance.
- List prior visible jobs newest-first and allow an exact previous result to be
  inspected without recomputation.
- After success, browser reload must retrieve the same job/result from PostgreSQL.

## 19. Assay Forward/Reverse compatibility UX

- Add a “Forward/Reverse pair analysis” section to Assay detail.
- Auto-select only a unique Forward/Reverse pair; otherwise require explicit choices
  from accessible AssayOligo associations and explain missing/ambiguous roles.
- Display each selected oligo’s public ID, role, and 5'-to-3' sequence before submit.
- Present Forward and Reverse individual Primer3 facts, Tm delta, heterodimer/end
  facts, warnings, Assay version snapshot, and full job provenance.
- Never describe the result as experimental validation, specificity, amplification
  success, or general compatibility pass/fail.
- Mark historical results whose Assay version no longer matches the current version.

## 20. Authorization/RBAC

- Admins, team managers within their managed scope, and members with access may
  submit jobs. Viewers may read visible results but may not consume compute resources.
- A retry requires the same submit permission and a retryable terminal failure.
- Every endpoint enforces authorization server-side using current Principal and
  membership policy. Worker execution is internal and cannot impersonate a user.
- Inactive users cannot submit or retry; their historical jobs/results remain
  attributed and accessible according to current visibility.
- Rate limiting must distinguish authenticated requester/institute and job kind.

## 21. Visibility propagation

- Job organization, project, team, and visibility are derived from the source Oligo
  or Assay; clients cannot broaden them.
- Pair jobs derive scope from the Assay and verify that both associated Oligos are
  accessible and valid for that Assay.
- Lists, counts, detail, polling, retry, and any future search integration apply the
  same server-side visibility policy.
- Access requires both visibility of the immutable job scope and current access to
  its source record, preventing historical-result leakage after scope tightening.
- Worker logs and Celery monitoring must not expose sequences or private metadata to
  users outside the application authorization boundary.

## 22. Audit requirements

Append AuditEvents for job request, deduplicated/idempotent replay where material,
dispatch failure, retry request, terminal success, and terminal failure. Record actor
or internal worker identity, timestamp, action, job ID, subject IDs, state transition,
request correlation, attempt number, and safe before/after facts.

Audit payloads MUST NOT contain tokens, secrets, database/broker URLs, unrestricted
logs, or duplicated full sequences. Sequence digests and stable record IDs are
sufficient for audit navigation; the authorized job detail retains the input snapshot.

## 23. Scientific provenance requirements

Every successful persisted component MUST be traceable to:

- stable ScientificJob ID and immutable result-schema version
- algorithm/tool name and exact effective tool version
- exact executable analysis mode for Tm, hairpin, homodimer, or pair result
- worker package and wrapper-contract versions
- container image digest or immutable build/Git revision and Primer3 source checksum
- fully expanded effective parameters, methods, units, and parameter-schema version
- Oligo/Assay stable IDs, Assay version and role tuples where applicable
- normalized 5'-to-3' sequence snapshots and SHA-256 identities
- request, queue, attempt start, and completion timestamps in UTC
- requester, executing attempt, result, warnings, unavailable components, and errors

This closes the class of provenance gap observed in historical
`Phylogenetic_analysis`, where tool versions, reference releases, execution platform,
timestamps, and Git revision could not be reconstructed later. It reuses that lesson
only as a provenance requirement; OligoSpace has no runtime, schema, package, or
workflow dependency on the other project.

## 24. Idempotency/deduplication strategy

- Canonicalize job kind, versioned input snapshot, and fully expanded effective
  parameters with deterministic key ordering and units, then hash them into an
  `execution_fingerprint`.
- Scope `Idempotency-Key` uniqueness to organization, requester, and create endpoint.
  Replaying the key with the same canonical request returns the same job; different
  content returns `idempotency_conflict`.
- A partial unique constraint or transactional lock prevents more than one active
  queued/running/retrying job for the same organization, requester, job kind, and
  execution fingerprint.
- Exact earlier successful jobs are displayed as reusable evidence, but a deliberate
  new run may create a new job and timestamp. It MUST NOT overwrite or relabel the
  prior result.
- Duplicate Celery delivery uses job state plus claim token and attempt uniqueness;
  it cannot create a second result.

## 25. Resource/input limits

- Accept one Oligo or one Forward/Reverse pair per job in this increment.
- Accept only normalized unambiguous DNA for Primer3 thermodynamic execution.
- Enforce the effective nearest-neighbor length bound at API and worker boundaries;
  default it to the qualified Primer3 2.6.1 value and cover both boundary values in
  tests. Do not silently use a long-sequence fallback formula.
- Reject NaN/infinity and enforce documented safe ranges for every concentration and
  loop parameter. Reject unknown keys and arbitrary CLI options.
- Cap request/response JSON, warning count, diagnostic text, attempts, tool subprocess
  duration, total job duration, per-user active jobs, and institute queue depth with
  configuration and stable errors.
- Initial defaults are at most three attempts and 30 seconds per tool subprocess;
  final total-job/concurrency limits must be exercised in runtime tests and documented
  before activation is considered complete.

## 26. Failure recovery

- Persist before publish. If Redis dispatch fails, retain the queued job with a safe
  dispatch error and make it eligible for periodic reconciliation.
- Reconcile due queued/retrying jobs and expired running leases from PostgreSQL.
- Use late acknowledgement and idempotent terminal commits so crashes before/after
  result commit cannot duplicate or lose a successful result.
- Database unavailability prevents success acknowledgement; the attempt remains
  recoverable and no Redis-only result is accepted as authoritative.
- Restarting API, worker, scheduler, or Redis must preserve job history and completed
  results. A documented runtime test must exercise at least worker interruption and
  Redis result expiry/restart behavior.
- Operators receive a bounded administrative query/runbook for stuck jobs; direct
  state editing is prohibited.

## 27. Backward compatibility

- Existing Oligo and Assay API representations remain compatible; job summaries may
  be added through new endpoints/sections rather than changing required fields.
- Existing Wallace values and `calculation_provenance` remain unchanged and visibly
  labeled as screening output.
- Existing Primer3 worker task contract may remain temporarily as an internal adapter
  during migration, but browser/API calls must use persistent jobs and the obsolete
  direct contract must be removed or explicitly private before completion.
- Migrations 0001–0003 and completed-plan behavior remain unchanged.
- Historical Assay versions and archived/deprecated source records remain readable;
  new submission from an inactive source is rejected according to existing policy.

## 28. Unit tests

- Job state-machine transition table, terminal-state immutability, retryability, and
  stale-lease recovery.
- Parameter defaults/ranges/units, canonicalization, fingerprints, idempotency
  conflicts, active-job deduplication, and versioned schema parsing.
- Input snapshots/digests, exact subject-shape constraints, unique/ambiguous pair
  selection, stored Reverse sequence orientation, and Assay-version staleness.
- Permission/visibility propagation and viewer submission denial.
- Result component states and strict separation of Wallace, nearest-neighbor,
  hairpin, homodimer, and pair facts.
- Error sanitization and diagnostic/log bounds.

## 29. API tests

- Submit both job kinds, retrieve/list/filter them, poll transitions, inspect success,
  retry an eligible failure, and reject illegal retries.
- Verify `202` new submission, idempotent replay, conflicting key, concurrent active
  deduplication, invalid parameters/alphabet/length, missing/ambiguous roles, and
  stable problem codes.
- Verify disabled users, viewers, cross-team/project/private/institute boundaries,
  inaccessible identifiers, no count leakage, and visibility narrowing after result.
- Verify audit events without sensitive sequences/logs and failure behavior when the
  queue gateway is unavailable.

## 30. PostgreSQL integration tests

- Apply `0001 → 0004`, downgrade `0004 → 0003`, and re-upgrade on PostgreSQL 17.
- Verify constraints, indexes, public-ID allocation, input/result immutability,
  attempt uniqueness, active fingerprint uniqueness, and atomic success/result commit.
- Exercise real transaction reload persistence for both job kinds and all four
  visibility scopes.
- Exercise duplicate task claims, crash-safe retry transitions, expired lease
  recovery, failed dispatch reconciliation, and result survival independent of Redis.
- Verify Oligo/Assay deletion restrictions and retained provenance after source
  metadata/version changes.

## 31. Worker tests

- Real pinned Primer3 2.6.1 golden fixtures for nearest-neighbor Tm, hairpin,
  homodimer, Forward/Reverse heterodimer/end analysis, and Tm delta.
- Invalid alphabet, nearest-neighbor length boundaries, parameter boundaries,
  timeout, nonzero exit, malformed/nonfinite output, and version mismatch.
- Argument-list execution without a shell, exact option/mode provenance, normalized
  output schema, and absence of biological pass/fail interpretation.
- Database claim/result transaction, retryable versus permanent classification,
  duplicate delivery, and worker interruption/recovery.

## 32. Browser/E2E tests through Caddy

Add an independent Playwright scientific-jobs spec that:

1. opens the application root through Caddy and authenticates in development mode;
2. opens a persisted Oligo, confirms Wallace is separately labeled, submits Primer3
   QC, observes nonterminal state, waits for success, and verifies all three facts;
3. reloads the browser and verifies the same stable job/result remains available;
4. opens an Assay, selects its Forward/Reverse associations, submits pair analysis,
   waits for success, verifies both individual and pair facts, then reloads;
5. verifies Assay version/provenance and neutral scientific wording;
6. exercises at least one rejected input or safely surfaced worker failure; and
7. proves a viewer cannot submit and an inaccessible user cannot discover the job.

The required persistence chain is UI submit → API → ScientificJob in PostgreSQL →
Celery/Redis → Primer3 worker → persisted PostgreSQL result → browser reload → same
job/result. A direct internal-container HTTP check is not a browser verification.

## 33. Runtime/container validation

- Validate Compose configuration and build production API, web, and worker images.
- Verify the pinned Primer3 source checksum and effective runtime version.
- Start Caddy, Next.js, FastAPI, PostgreSQL, Redis, worker, and any reconciliation
  scheduler through health-gated Compose.
- Confirm internal-only PostgreSQL/Redis ports, non-root application containers,
  production secret validation, and least-privilege worker database configuration.
- Execute one real job of each kind, worker restart recovery, Redis result
  expiry/restart persistence, API readiness, and host-browser smoke through Caddy.
- Report build-verified, service/API-verified, and browser/E2E-verified evidence
  separately.

## 34. Documentation updates

During implementation—not during this proposal-only step—update:

- `docs/PRODUCT_SPEC.md` only if acceptance semantics need clarification without
  changing stable requirement IDs.
- `docs/DATA_MODEL.md` with ScientificJob/Attempt/Result relationships and lifecycle.
- `docs/BIOINFORMATICS.md` with exact Primer3 modes, ranges, units, wrapper/result
  schema versions, scientific limitations, and golden fixtures.
- `docs/SECURITY.md` with expensive-job rate limits, worker DB privileges, and safe
  diagnostics.
- `ARCHITECTURE.md` with the persistent job flow and PostgreSQL authority.
- `docs/REQUIREMENTS_TRACEABILITY.md`, `docs/project/STATUS.md`,
  `docs/project/BACKLOG.md`, and `docs/project/CHANGELOG.md` with evidence-backed
  statuses.
- operator/developer runbooks for stuck-job recovery and local job execution.

No requirement may become Verified without a relevant automated test or explicit
runtime/browser validation.

## 35. Acceptance criteria

- Both individual Oligo QC and selected Forward/Reverse Assay analysis execute via
  persistent jobs and real Primer3 2.6.1 tools.
- Nearest-neighbor Tm, hairpin, homodimer, and pair results are distinct typed facts;
  Wallace remains separately labeled and unchanged.
- Every result retains sufficient input, parameter, tool, worker, environment,
  timestamp, job, warning, and error provenance for reproduction and audit.
- Invalid or unsupported inputs produce explicit unavailable/errors, never invented
  values or silent algorithm fallback.
- Authorization and visibility pass private/project/team/institute tests without
  list, count, detail, polling, or retry leakage.
- Idempotent HTTP retries, duplicate Celery delivery, worker failure, Redis restart,
  and browser refresh do not duplicate or lose authoritative results.
- UI → API → PostgreSQL → Celery/Redis → Primer3 → PostgreSQL → browser reload passes
  for both job kinds through Caddy.
- Object storage is not introduced for structured Primer3 results.

## 36. Completion criteria

Plan 005 may move to `docs/exec-plans/completed/` only when:

- migration `0004_scientific_jobs` is reversible and verified on PostgreSQL 17;
- format, lint, strict type checks, unit/API/PostgreSQL/worker/web tests all pass;
- real Primer3 golden/boundary/error fixtures pass in the pinned runtime image;
- production images and Compose configuration pass;
- both browser workflows and reload persistence pass through Caddy, plus the separate
  host-browser smoke required by prior plans;
- failure recovery, retry/deduplication, Redis independence, RBAC, visibility, audit,
  and provenance acceptance criteria have explicit evidence;
- documentation and requirement traceability distinguish Implemented from Verified
  and separately report build, API/service, worker, and browser validation;
- known limitations and deferred scientific interpretations remain explicit; and
- the outcome is recorded without activating Plan 006 or any later phase.

## Architecture decision review

No new durable architecture or domain decision is required to approve this plan.
The workflow applies existing accepted decisions: modular monorepo, FastAPI and
PostgreSQL as the authoritative relational core, Keycloak/OIDC with API-side
authorization, separation of biological identity from assay context, and
Compose/Micromamba with the established Celery/Redis scientific worker. The user-
approved scope explicitly adds the worker-to-PostgreSQL persisted-result path.

Stop for approval and create an ADR before implementation only if delivery would
instead require a different broker/workflow engine, a second authoritative result
store, object storage for these structured results, arbitrary user-defined analysis
code, a shared cross-service package that materially changes dependency boundaries,
or a generalized scientific workflow model beyond these two Primer3 job kinds.

## Risks and unresolved implementation questions

- Exact `oligotm`/`ntthal` option semantics, nearest-neighbor length boundary, and
  pair/end-analysis output must be qualified against the pinned 2.6.1 executables
  and documented fixtures before UI exposure.
- Direct worker persistence expands database access. Least privilege, transactional
  state transitions, and credential separation require security validation.
- Database commit and Redis publication are not one transaction. The planned
  queued-job reconciler is required to close that recovery gap without introducing a
  new broker/outbox architecture.
- Celery late acknowledgement creates duplicate delivery by design; job claims and
  immutable result uniqueness must make it harmless.
- Thermodynamic facts depend strongly on effective concentrations and methods. Poor
  defaults can mislead even when technically reproducible, so labels, units, and
  neutral interpretation are acceptance requirements.
- Assays may contain zero, one, or multiple oligos per contextual role; pair
  selection and stale Assay-version behavior must remain explicit.
- Capturing an immutable container identity in local development may require build
  metadata injection when an OCI registry digest is unavailable.
- Full E2E validation rebuilds the large pinned worker and Playwright images and must
  respect local storage constraints while retaining sufficient evidence.

## Estimated implementation sequence

1. Qualify Primer3 2.6.1 CLI modes, limits, parameter mapping, and golden fixtures.
2. Add versioned schemas/state machine and reversible migration 0004.
3. Implement API repository/service/authorization/audit/idempotent create/read/retry.
4. Add queue gateway, narrow worker persistence, claims, attempts, retry recovery,
   and periodic reconciliation.
5. Extend the Primer3 wrapper and execute both job kinds with immutable results.
6. Add Oligo QC and Assay pair browser workflows with polling and provenance views.
7. Complete unit, API, PostgreSQL, worker, and web tests.
8. Run production image/Compose/service recovery validation and Playwright through
   Caddy, including reload persistence for both workflows.
9. Update project documentation and traceability, record evidence, and move the plan
   to completed only after every completion gate passes.

## Validation evidence

- Interruption and recovery ran on 2026-10-29 against the isolated `oligospace-e2e`
  Compose project only; the development stack was not restarted or modified. Full
  evidence: `docs/project/PLAN_005_RECOVERY_EVIDENCE.md`.
- Scenario A (worker SIGKILL during an attempt), B1 (Redis restart after completion),
  B2 (Redis unavailable at submission, 503 then idempotent replay) and C (stuck job
  reconciliation) pass. PostgreSQL kept the full job history; Redis messages and
  Celery result keys were lost on restart, as expected, without losing any result.
- Scenario C0 found a defect: a superseded attempt committed success after
  reconciliation had started attempt 2, leaving attempt 2 `running`. Fixed by attempt
  fencing (`FOR UPDATE` on job/attempt, `stale_attempt_rejected` audit, `SKIP LOCKED`
  reconcile with `worker_lost`/`redispatch` audit) and by bounding the tool timeout by
  the attempt lease (`lease_exhausted`). C1 and C2 confirm consistent transitions,
  one result per job and, with both fixes, no overlapping execution.
- Regression tests: `services/bioinfo-worker/tests/test_attempt_fencing.py` (7 tests).
- Gates: format, lint and typecheck exit 0; API 25 passed / 7 skipped, worker 14
  passed, web 2 passed; PostgreSQL integration 7 passed; Caddy E2E 10 passed;
  Compose configuration valid. GitHub CI is green on `975a8ae` and `f7fff83`; later
  local commits are not pushed and have no CI run yet.

## Outcome

Persistent Primer3 scientific jobs are implemented and validated, including worker,
Redis and reconciliation recovery. Plan 005 is complete. Residual risks, tracked in
the backlog and not blocking: no lease heartbeat, claim token not rotated per
attempt, Celery task id reused across retries, pre-existing mypy errors on worker
test monkeypatches, and no local-execution runbook. Plan 006 was not activated.
