# MVP-02 — Scientific end-to-end acceptance

Date: 2026-11-08. Base: `5e343407c8c998e7a8a844424bf90faba4b00272`.
Branch: `codex/mvp-02-scientific-acceptance`. Acceptance is pending the runtime
results below and human scientific review; this is not pilot/deployment approval.

## Existing scope and qualification matrix

MVP-01 is integrated via PR19 (`dc012e8`). Registry lifecycle, current membership
authorization, contextual AssayOligo roles, search, immutable biological identity,
scientific jobs and visible/filtered oligo CSV already exist. MVP-02 reuses them.

| Journey | Acceptance evidence | Current execution |
|---|---|---|
| Real OIDC login; authorized institute/team/project | Five synthetic Keycloak identities; scientist creates project through UI; existing MVP-01 16-case suite remains separate | Pending scientific runtime / CI |
| Target create/edit; stable ID and persistence | UI registration/edit, reload, gene search | Pending Chromium |
| Oligo sequences/metadata/IDs | Independent length/GC/Wallace/mass/reverse-complement comparison, normalization, duplicates, immutable sequence, notes and reload | Pending Chromium; PostgreSQL suite passes |
| Assay roles, versions and reuse | Invalid PCR role/repeated association refusals; two assays reuse existing oligos; version 2 persists | Pending Chromium; existing PostgreSQL contracts retained |
| Search/filter/detail | Sequence/name/gene queries, empty results, project/global navigation | Pending Chromium |
| Primer3 QC and pair | Pinned 2.6.1, checksum, default parameters, nine reference facts within 1e-6 °C, stored snapshot/attempts/result and fresh login | Pending real worker |
| Controlled parameters | Explicit 75 mM salt request is separately recorded; inconsistent request refused without job; golden fixture unchanged | Pending Chromium |
| Async/repeated submissions | Worker stopped: queued, reload, six requests/one active job; worker restart: one successful attempt/result | Pending Chromium; two new PostgreSQL regressions pass |
| Collaboration and current rights | Admin/editor/reader plus second institute; direct APIs, private records, job reads/submission/retry, membership removal/regrant and role demotion | Pending Chromium |
| Failure handling | Ambiguous/long DNA, invalid parameters, missing reverse role, unknown IDs; controlled failing executable in disposable worker, terminal failed state and absent result after reload | Pending Chromium |
| CSV fidelity and permissions | Real download and parser, source-field comparison, Unicode/quoting/formula protection, empty/filter/private/institute/revoked access | Pending Chromium; existing PostgreSQL CSV contracts retained |
| Desktop/mobile usability | Seven screens at Pixel 7 and 1440/1024/768 px, navigation, required/invalid fields, result readability, overflow and synthetic captures | Pending Chromium |

## Anomalies and changes

1. A fresh idempotency key bypassed active-request reuse, reaching the existing
   unique index and returning an integrity error. Active identical requests now
   reuse the queued/running/retrying job even with a new key. Concurrent initial
   inserts recover the winning job after rollback. Existing fingerprint/key
   conflicts remain 409; no scientific parameter, result or schema is changed.
   PostgreSQL tests cover sequential clicks, overlapping initial submissions,
   one persisted job and one dispatch.
2. Independent review found stale scientific evidence could survive an early failed
   rerun. Scientific JSON and screenshots are now cleared before each execution.
3. Existing local scientific scenarios were not connected to the OIDC harness.
   `run.py --scientific` supplies isolated Redis/worker/scheduler and five actual
   OIDC identities in two institutes. Authentication-only execution remains scoped
   to its original tests. No development-identity rehearsal qualifies this report.

## Validation results and reproducibility

- PostgreSQL: **206 passed**, zero skipped, with fresh PostgreSQL 17 and Alembic
  `0001` → `0004`, downgrade to `0003`, upgrade to head; test container removed.
- Backend/worker: Ruff format/lint and mypy pass; **99 API units**, **14 worker
  units** pass. The 206 integration cases are intentionally skipped by the unit
  invocation and executed by the dedicated suite above.
- Current frontend source: TypeScript passes; **15 web units** pass with Node
  22.23.2. Cached tooling results are not used as proof for current web source.
- Harnais/log policy: **12 tests pass**. No raw errors/tokens/HTTP traces are
  retained by the OIDC reporter.
- Standard `make format lint typecheck test PYTHON_RUNNER=container` was attempted;
  frontend image dependency download hit npm `ETIMEDOUT` before tests. No dependency
  downgrade or security-gate bypass was applied. Exact-head CI and runtime pending.

Run `python3 infra/auth-qualification/run.py --scientific` for the new isolated
campaign. It uses randomly named Compose resources, private networking, tmpfs data,
generated temporary credentials/certificate, production API/web and real Keycloak.
It never reads `.env`, shares development volumes, or publishes ports. Only its
own resources are torn down. `summary.json`, scientific aggregates, secret-log
gate and synthetic result screenshots are retained in the CI artifact
`mvp02-scientific-evidence`. No real biological data is used.

Validated numerical reference: [Primer3 qualification](../PRIMER3_QUALIFICATION.md).
These thermodynamic facts do not establish amplification, specificity or biological
validation. Wallace remains separately identified screening data.

## Independent review

Read-only independent review examined production idempotency, PostgreSQL tests,
scientific browser suite, harness and workflow. Its stale-evidence finding was
corrected. It also identified absent terminal worker-failure coverage; a real
worker fault-injection scenario was added, with restoration in `finally`. Runtime
proof remains pending; code review alone is not execution evidence.

## Missing capabilities, coverage limits and acceptance gates

No new registry, export format, upload or scientific architecture is needed for
the explicitly requested journey. Inventory/orders/QR, full reference ingestion,
persisted mapping/GeneOligoViewer and BLAST remain outside the delivered MVP subset.
Experiment runs/contextual validation retain existing regression coverage and do
not substitute for scientific acceptance of a curated real dataset.

Browser initial-insert contention is tested separately by real PostgreSQL
integration; browser repeated submissions start with a queued job. Mobile uses
Chromium device emulation, not a physical device. Human usability, assistive
technology, institutional realm policies and a scientist-approved dataset are not
qualified by synthetic automation. Worker lease/claim-token/retry debt remains
recorded; no broader concurrency or recovery guarantee is inferred.

Before MVP acceptance: finish current Chromium/OIDC/scientific and exact-head CI,
resolve demonstrated failures, review this dossier and synthetic captures, then
obtain human scientific acceptance (R1-10/11). Hosting/backup/TLS operational gates
R1-08/09 and all DEPLOY-02 findings remain independent and open. No Mac mini,
Cloudflare, SeaweedFS adoption, release publication or automatic merge occurred.
