# MVP-02 — Scientific end-to-end acceptance

Date: 2026-11-08. Base: `5e343407c8c998e7a8a844424bf90faba4b00272`.
Single branch: `codex/mvp-02-scientific-acceptance`.
Delivery: [PR #20](https://github.com/El-Castor/OligoSpace/pull/20), without merge.

**The seven automated scientific journeys pass on a disposable real OIDC stack.**
This qualifies the delivered functional subset with synthetic data. Human scientific
acceptance and hosted-pilot/security approval remain separate, unfulfilled gates.

## Existing scope and acceptance matrix

MVP-01 is integrated via PR19 (`dc012e8`). Registry lifecycle, membership-based
permissions, contextual AssayOligo roles, search, immutable sequence identity,
persistent scientific jobs and visible/filtered oligo CSV already existed.
MVP-02 reuses these capabilities; it does not reimplement them.

| Journey | Verified behavior | Evidence/result |
|---|---|---|
| OIDC and workspace | Five real Keycloak identities in two institutes; scientist creates a project through UI in an authorized team | PASS scientific suite; 16 existing OIDC tests also PASS |
| Targets | Create, edit, immutable public ID, gene search, notes after reload | PASS Chromium/OIDC |
| Oligos | Normalization; independent length, GC, Wallace Tm, mass and reverse-complement checks; metadata, IDs, duplicate/reverse-complement guidance, immutable sequence | PASS Chromium/OIDC and PostgreSQL |
| Assays and reuse | Invalid PCR role/repeated association refusal; forward/reverse roles, target link, version 2 persistence; reuse the same oligos in another assay | PASS Chromium/OIDC and PostgreSQL |
| Discovery | Name/sequence/gene filtering, empty results, project and global search, detail navigation | PASS Chromium/OIDC |
| Primer3 QC and pair | Real worker, version 2.6.1 and source checksum; nine golden facts; exact snapshots, parameters, attempts/provenance and results persist across reload and fresh login | PASS; maximum absolute numeric difference **0 °C**, tolerance 1e-6 °C |
| Controlled parameters | Separate explicit 75 mM salt request is recorded and changes Tm; inconsistent parameters refused without job | PASS; golden reference parameters unchanged |
| Async and repeats | Stop disposable worker, submit and reload queued job, repeat with fresh keys; restart worker and read completed result | PASS; **6 requests, 1 job, 0 server errors**, one successful attempt |
| Collaboration | Admin/editor/reader and another institute; private resources, direct APIs, result access, viewer submission/retry denial, membership removal/regrant and global-role demotion | PASS; **13 denials and 9 cross-institute checks**; revoke/demotion effective |
| Failure and persistence | Ambiguous/long DNA, invalid parameters, missing reverse role, unknown IDs; real worker executable fault produces terminal failed job without result, retained after reload | PASS; executable restored in test finally |
| CSV | Actual browser download, all 16 columns checked, five rows with Unicode/quotes/formula/zero/null data; filtered/empty/private/reader/foreign/revoked access | PASS; **5 source rows, 0 field mismatches, 0 excluded records leaked** |
| CSV history | Query persisted PostgreSQL audits for every tested download, including actor, exact row count, schema and distinct request correlation | PASS enhanced local gate; six exact ordered audits, detailed below |
| Desktop/mobile | Seven screens on Pixel 7 emulation; same seven screens at 1440/1024/768 px, navigation, required/invalid input, readable results, page identity, no uncaught JS exception | PASS; **7 mobile + 21 desktop screen checks, 0 horizontal overflows** |

Scientific setup uses synthetic accounts and a PCR catalogue fixture with the
existing forward/reverse role rules. Account/institute/team setup is an explicit
test fixture; the scientist performs project creation and scientific operations
through ordinary authenticated application controls.

## Observed anomalies and corrections

1. **Repeated scientific submission could raise an integrity error.** A fresh
   idempotency key bypassed active-request reuse and hit the existing unique
   index. Identical queued/running/retrying requests now return the active job
   even with a new key. Concurrent first inserts recover the winning job after
   rollback. Different fingerprints with an already-used key still return 409.
   Both new regressions fail on original main with
   `uq_scientific_jobs_active_fingerprint`; they pass with the fix. Exactly one
   job and one dispatch are asserted against PostgreSQL. No schema, scientific
   parameter or calculation change was necessary.
2. **Scientific runtime evidence could be stale after an early failed rerun.**
   Independent review found missing cleanup of scientific JSON/screenshots.
   They and the audit proof are now removed before each execution.
3. **Existing scientific scenarios were disconnected from real OIDC services.**
   The dedicated mode now starts isolated Redis/worker/scheduler, uses five actual
   OIDC identities and supports controlled worker stop/start/fault/repair. No
   development-identity rehearsal is accepted as scientific OIDC proof.
4. **Acceptance assertions assumed unsupported presentation behavior.** The first
   CI run passed four scenarios and exposed two browser HTTP-404 assumptions plus
   an export-in-dashboard assertion. Next can stream a 200 before rendering its
   not-found boundary. Browser denial now requires the rendered 404 boundary and
   no resource/job content; direct protected APIs still require 404. Export events
   are persisted but deliberately excluded from the resource activity panel;
   audit verification queries PostgreSQL instead of adding new product behavior.
5. **Audit proof was initially too weak.** Independent review required verification
   of every tested download. The final gate requires six distinct request IDs and
   this exact chronological `(actor, row_count)` sequence: reader/0 after revoke;
   scientist/5 browser download; scientist/1 filtered; scientist/0 empty; reader/4
   with private data excluded; rival/0. Wrong actor/count, missing events, reused
   correlation, invalid schema and unexpected evidence fields fail dedicated tests.

No production UI defect requiring a design change was observed. The existing
Scientific Soft UI is preserved. Oligo viewer edit navigation remains the known
UI debt: read-only forms and server-side write/compute refusal are enforced.

## Executed validation

| Check | Result |
|---|---|
| `make format lint typecheck test PYTHON_RUNNER=container` | PASS; 99 API, 14 worker, 15 web units; Ruff and mypy/TypeScript pass |
| `make test-integration` | **206 passed, 0 skipped**; fresh PostgreSQL 17, Alembic 0001→0004, downgrade to 0003 and upgrade to head; test container removed |
| `make test-e2e` | **29 Chromium tests passed** through Caddy; isolated development-auth regression stack torn down |
| `make compose-config` | PASS; no existing deployment definition changed |
| Harness/log/evidence unit tests | **16 passed**, including four strengthened CSV-audit gate tests |
| Local real HTTPS/Keycloak + PostgreSQL + scientific worker | **7/7 passed**, ARM64; enhanced CSV-audit and log gates PASS |
| [CI scientific run 42527193283](https://github.com/El-Castor/OligoSpace/actions/runs/42527193283) | **7/7 PASS** on clean `428e58f07d9d2a35d09187c5d708e37a4a21977a`, x86_64 |
| [CI application 42527193294](https://github.com/El-Castor/OligoSpace/actions/runs/42527193294) | All six application jobs PASS |
| [CI OIDC 42527193346](https://github.com/El-Castor/OligoSpace/actions/runs/42527193346) | Existing **16 real OIDC tests PASS** |
| [CI Chromium job](https://github.com/El-Castor/OligoSpace/actions/runs/42527193286/job/128873301149) | Existing **29 Chromium tests PASS** |

Initial local image builds hit npm download `ETIMEDOUT`; retry after the dependency
became available passed. No downgrade, scientific adjustment or security bypass
was applied. Local source-only lint also passed while ignoring generated
`prototype/.next/**`; standard clean-container lint subsequently passed normally.
The final delivery SHA and its complete CI conclusions are recorded on PR #20;
the retained snapshot below explicitly names the earlier clean qualified SHA.

Existing DEPLOY-triggered jobs remain red: API/worker native image security,
baseline-secret triage and candidate-storage/source qualification. Their failure
is **not** a green overall CI or pilot acceptance. They were not disabled,
reconfigured or remediated in this scientific lot. See the existing
[DEPLOY-02 dossier](../deployment/DEPLOY_02_SECURITY_REMEDIATION.md).

## Evidence and reproduction

Run `python3 infra/auth-qualification/run.py --scientific`. It generates a randomly
named Compose project, private internal network, tmpfs databases, temporary
credentials/certificate, production API/web and real Keycloak plus worker/scheduler.
It never reads `.env`, shares development volumes, or publishes ports. Teardown
only removes that disposable project's resources. Authentication-only execution
retains its original separate 16-test suite.

[Retained evidence](evidence/mvp02/summary.json) is from clean CI `428e58f`:
[scientific aggregates](evidence/mvp02/scientific-evidence.json),
[secret-log gate](evidence/mvp02/secret-log-gate.json),
[mobile capture](evidence/mvp02/synthetic-scientific-mobile.png), and
[desktop capture](evidence/mvp02/synthetic-scientific-desktop.png).
The [enhanced local audit proof](evidence/mvp02/csv-audit-local.json) records the
subsequent six-download gate exercised in the working tree delivered by this PR;
it is distinct from the earlier CI snapshot. Files are indexed in
[SHA256SUMS](evidence/mvp02/SHA256SUMS). Final CI also retains its exact-commit,
timestamped sanitized artifact `mvp02-scientific-evidence` for 14 days.
No raw credentials, HTTP traces, token-bearing exceptions or real biological data
are retained. API/web/Keycloak/Caddy/worker/scheduler log-secret gates pass.

Scientific reference: [Primer3 qualification](../PRIMER3_QUALIFICATION.md),
version 2.6.1, source SHA256
`805cef7ef39607cd40f0f5bb8b32e35e20007153a0a55131dd430ce644c8fb9e`.
Reference parameters remain 50 mM monovalent, 1.5 mM divalent, 0.6 mM dNTP,
50 nM oligo, loop 30; stored methods/units are checked. These thermodynamic facts
establish neither amplification nor specificity nor biological validation.
Wallace remains separately labelled screening data.

## Independent review

A separate reviewer examined production idempotency, PostgreSQL regressions,
browser tests, evidence handling, isolation and workflow. Stale-evidence and weak
CSV-audit findings were corrected and re-reviewed. The final review reports both
resolved and no further concrete findings. Runtime proof is independently listed
above; review alone is not execution evidence.

## Missing functionality, coverage limits and remaining acceptance

No additional registry function, upload or export format is needed for the
explicitly requested delivered-subset journey. Inventory/orders/QR, governed
reference ingestion, full persisted mapping/GeneOligoViewer and BLAST remain
unimplemented later work, outside this qualification. Experiment runs/contextual
validation retain existing real PostgreSQL/Chromium regression coverage; no new
clinical or experimental conclusion is inferred from the synthetic fixtures.

Browser repeats start with one queued job; competing initial inserts are covered
separately by PostgreSQL integration. Mobile means Chromium device emulation,
not a physical phone. Synthetic automation does not qualify human usability,
assistive technology, an institutional realm or scientist-approved real data.
Worker lease/claim-token/retry debt remains recorded; a stopped-worker recovery
is not an exhaustive concurrency/crash-recovery guarantee. The CSV scope is oligos
and their stored QC/provenance, not a new Primer3-result CSV format.

Before full MVP acceptance, review this dossier and captures and obtain owner
approval of curated data and human scientific acceptance (R1-10/11). Hosted-pilot
backup/TLS/operations R1-08/09 and all DEPLOY-02 security gates remain open. No
Mac mini access/deployment, Cloudflare change, SeaweedFS adoption, release or
merge was performed. Stop after PR/CI/report delivery for user review.
