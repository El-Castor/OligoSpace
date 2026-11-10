# DEPLOY-03 — Container hardening and security remediation

Status: **technical qualification completed for code review; release/pilot blocked** (2026-11-10).
Single branch `codex/deploy-03-container-hardening`, [PR #21](https://github.com/El-Castor/OligoSpace/pull/21),
from verified main `9ebbf2cd993395af2b154efb0b4cf5a76b4dd079`.
Ubuntu LTS has been selected after native comparison; production Dockerfiles and their consumers are updated, with final native artifact qualification recorded below. No image publication,
deployment, real-data migration, Cloudflare change or S3 provider adoption.

## Reproducible initial inventory

Historical DEPLOY-02 receipts distinguish **nine distinct HIGH Debian CVEs** from
**176 HIGH binary-package occurrences** across API/worker × AMD64/ARM64 (44 each).
The deterministic normalizer and retained inventory are in
[`infra/hardening`](../../infra/hardening/). Historical absent CVSS, severity source,
layer and usage evidence remain unknown, rather than invented or treated as zero.
Existing technical-failure scans are retained as `not_verified`.

Fresh native ARM64 baseline artifacts were exported before production changes,
with provenance/SBOM and exact OCI manifest/config/rootfs identity verified.
Docker Desktop 29 identifies a selected image by manifest rather than legacy
config ID: loading now uses the **same exported OCI**, with platform-specific
inspection and exact manifest/config-bound layer identity, instead of rebuilding.

| Frozen baseline | Critical | High | Medium | Low | Unknown | Inventory | Secrets |
|---|---:|---:|---:|---:|---:|---:|---:|
| API ARM64 | 0 | 46 | 82 | 66 | 0 | 160 | 0 |
| Worker ARM64 | 0 | 46 | 81 | 65 | 0 | 127 | 0 |

Receipts: [API](../../infra/hardening/evidence/baseline-arm64-api.json),
[worker](../../infra/hardening/evidence/baseline-arm64-worker.json).
Trivy digest `790fd66d1697395d8693d1acaa1ea702406a20f109b6fc7bac8db623eca6c06c`;
frozen DB SHA256 `b6ce84ecc46809205903624249d7bf688ca3e06e1b75d3683f4ffbda912eb872`.
Both run with network disabled, read-only DB and pre/post identity verification.
Full package inventory and OS coverage are observed. All severities and secrets
still block the release scan gate; comparison exit code 2 is an observed failed
gate, never a security waiver.

The fresh database reports **11 distinct HIGH IDs**, adding SQLite
`CVE-2026-119374` and `CVE-2026-119379` to the historical nine. This is a dated
finding-set change, not proof of an application regression. The per-CVE review
records source packages, CVSS vendor, available distribution fixes, execution
preconditions and uncertainty in [advisory-review.json](../../infra/hardening/evidence/advisory-review.json).
Debian urgency/no-DSA/postponement are not interpreted as CVSS, fixes or acceptance.
The contradictory tracker annotation for `CVE-2026-78409` is explicitly unresolved.

## Three-way experiment

| Strategy | Construction | Maintenance / risk | Current decision |
|---|---|---|---|
| A | Original micromamba plus removal of development Python tooling | Same maintained trixie baseline; lower-layer bytes remain in OCI | No HIGH reduction; Tk closure unresolved |
| B | Same `/opt/conda` prefix and scientific artifacts copied into pinned trixie-slim | Retains real Conda activation and metadata | Adds two HIGH occurrences; Tk closure unresolved |
| C | Pinned official Python 3.12.16 slim-bookworm; hashed wheels; separate Primer3 builder | Maintained glibc distribution; Python patch change qualified against golden values | Adds two CRITICAL findings; `_tkinter` closure unresolved |
| C / Ubuntu | Pinned Ubuntu 24.04; maintained distro Python 3.12; same hashed runtime wheels | Distro security backports, no Conda; vendor CVE coverage needs cross-check | Selected after four native runtime passes; final artifacts under qualification |

Recipes are experiments under `infra/hardening/strategies`, not production images.
Native CI compares all severities, full inventories, SBOM/provenance, final OCI
bytes, imports, dynamic libraries, CA trust, actual default entrypoint, non-root
read-only execution, nine Primer3 golden facts and a synthetic BLAST exact match.
Selection follows those observations. Bookworm support ending before trixie and
scientific archive provenance remain explicit tradeoffs.

The first three strategies completed natively on both architectures in
[run 42644332091](https://github.com/El-Castor/OligoSpace/actions/runs/42644332091).
[Full receipts and aggregate](../../infra/hardening/evidence/comparison-9020258/summary.json)
use one identical frozen vulnerability DB across all 16 artifacts. OCI sizes below
are exported archive MiB, not uncompressed image or peak build disk use.

| Role / architecture | Baseline | A | B | C Bookworm |
|---|---:|---:|---:|---:|
| API AMD64 | 219.13 | 219.04 | 172.69 | 91.55 |
| API ARM64 | 175.85 | 175.76 | 129.78 | 90.47 |
| Worker AMD64 | 509.64 | 509.55 | 463.30 | 382.35 |
| Worker ARM64 | 414.80 | 414.71 | 368.84 | 329.71 |

Severity totals are identical between architectures in that run:

| Image / strategy | Critical | High | Medium | Low | Unknown | Trivy inventory / SBOM components |
|---|---:|---:|---:|---:|---:|---:|
| API baseline | 0 | 46 | 82 | 66 | 0 | 160 / 208 |
| API A | 0 | 46 | 81 | 66 | 0 | 150 / 198 |
| API B | 0 | 48 | 87 | 67 | 0 | 153 / 201 |
| API C | 2 | 40 | 129 | 111 | 0 | 164 / 178 |
| Worker baseline | 0 | 46 | 81 | 65 | 0 | 127 / 175 |
| Worker A | 0 | 46 | 80 | 65 | 0 | 118 / 166 |
| Worker B | 0 | 48 | 86 | 66 | 0 | 121 / 169 |
| Worker C | 2 | 40 | 132 | 112 | 0 | 133 / 147 |

All eight worker executions reproduce the nine golden values, BLAST fixture and
timeout/error classification. Every initial strategy still fails exhaustive native
library closure because optional Tk components refer to unavailable libraries.
No missing library was deleted or filtered from the gate. C's two CRITICAL IDs are
`CVE-2025-7458` (SQLite) and `CVE-2023-45853` (zlib); lower size/HIGH count therefore
does not establish a better security result. Different Trivy/SBOM counts describe
different inventories, not interchangeable coverage metrics; retained Conda
components have visibility limits and must not be silently treated as scanned.

[Official Ubuntu advisory review](../../infra/hardening/evidence/ubuntu-advisory-review.json)
keeps six baseline HIGH IDs at `needs-evaluation`, one at `ignored`, one vendor
`not-affected`, and three with distro fixes to verify against the installed image.
Both Bookworm CRITICAL IDs are vendor `not-affected` on Noble. Vendor statements
are distinguished from observed installed versions and from scanner severity.
A quiet Ubuntu scan will not close unresolved upstream/source-package questions.

## Selected runtime and final changes

Ubuntu selection evidence is retained from native
[run 42647176195](https://github.com/El-Castor/OligoSpace/actions/runs/42647176195)
at `74e8d4c8498d72559eaa27bf3e8dbee39386b91b`, before final packaging changes.
Both roles passed import/complete library closure, CA, non-root, rootfs read-only,
capability and NNP probes on AMD64 and ARM64. Both workers passed the nine unchanged
Primer3 facts, BLAST exact-match fixture and timeout/exit classification.
[Receipts](../../infra/hardening/evidence/ubuntu-selection-74e8d4c/summary.json).

| Selection artifact | OCI MiB | Critical / High / Medium / Low / Unknown | Packages |
|---|---:|---|---:|
| API AMD64 | 93.09 | 0 / 0 / 23 / 7 / 0 | 167 |
| API ARM64 | 91.30 | 0 / 0 / 23 / 7 / 0 | 167 |
| Worker AMD64 | 383.73 | 0 / 0 / 22 / 6 / 0 | 135 |
| Worker ARM64 | 330.37 | 0 / 0 / 22 / 6 / 0 | 135 |

Final packaging uses a signed Ubuntu snapshot `20261109T120000Z`, exact hashed
wheels and separate `tooling`/default `runtime` targets. Pip is removed before
copying the runtime environment, rather than hidden beneath a deletion layer;
compilers and the distro pip-wheel/venv installation packages stay in build/tooling
stages. Runtime application metadata, apt inventory and scientific legal files stay
present. Both final images use UID/GID 1000. Direct commands replace activation
wrappers; migration policy still requires one exact command and rejects shell,
extra arguments, downgrade and legacy command variants.

Two scoped API updates address observed fixable advisories: PyJWT 2.14.0→2.15.0
(`CVE-2026-101918`, `CVE-2026-102275`) and python-multipart 0.0.30→0.0.31
(`CVE-2026-53540`). Baseline locks/graphs are preserved, derived inputs document
exact changes, and all other API runtime versions including Kombu 5.6.2 are unchanged.
Final native OIDC/application proof is recorded below.

The final cross-check found a maintainer HIGH advisory absent from the retained
Trivy scan: [GHSA-cxcq-r753-xf25](https://github.com/biopython/biopython/security/advisories/GHSA-cxcq-r753-xf25),
CVSS 8.8, affects Biopython below 1.88. The worker is therefore updated from
1.85 to 1.88 with exact PyPI hashes; NumPy 2.5.4 and every other worker pin stay
unchanged. No direct Bio import exists in the application worker source, and no
scientific algorithm or reference is changed. Qualification additionally imports
Bio/NumPy and records their actual versions. Earlier runtime evidence is explicitly
retained as pre-update evidence, not proof of the corrected dependency.

Scanner severity is not a cross-vendor CVSS normalization: two retained GnuTLS
findings classified MEDIUM carry Red Hat CVSS 7.4. They remain open, without a
fixed version demonstrated in the maintained image; Ubuntu's published assessment
and upstream disagreement are recorded separately. Thus “zero detected HIGH”
never means “all high-scoring upstream risks eliminated”.
[Supplement and provenance](../../infra/hardening/evidence/upstream-supplement.json).

The minimal base initially failed snapshot HTTPS because no CA store existed.
BuildKit now downloads a fixed official Ubuntu CA package with SHA256 verification;
only public trust anchors bootstrap HTTPS. Normal TLS and signed apt verification
remain enabled, and apt installs the canonical snapshot CA package.
[Bootstrap provenance](../../infra/hardening/evidence/ca-bootstrap.json).
The native tooling checkout ownership failure was corrected by running tooling
with the checkout owner's UID/GID; deployed runtime identity is unaffected.

Container construction decision: [ADR-0008](../decisions/ADR-0008-maintained-python-runtime.md).
Legacy Conda files remain optional local environments, not the container source of
truth. Distro Python reports 3.12.3 with Ubuntu security backports; its installed
package version is recorded separately. Both pyprojects permit Python 3.12.

Independent code review found and resolved two P2 issues (log retrieval could
falsely prove absence; Ubuntu split versions were truncated). Final implementation
and CA-bootstrap follow-up found no further critical/important issue. This review
does not replace native execution or human acceptance.
[Review record](../../infra/hardening/evidence/independent-review.json).

## Runtime and scientific qualification

Isolated qualification declares non-root execution, capability removal,
`no-new-privileges`, read-only root, bounded tmpfs, CPU/memory/PID limits, internal
network, no host ports, no privileged services and no Docker socket. Runtime
inspection verifies actual settings separately from the Compose declaration.
Generated disposable credentials use private files; no credential values are
retained in reports. [Runtime procedure](../../infra/hardening/ISOLATED_RUNTIME.md).
Full OIDC/scientific harnesses now offer an isolated `--hardened` mode; scientific
failure injection recreates only the disposable worker with a read-only fixture,
then restores the original configuration, instead of modifying its root filesystem.

Initial ARM64 baseline worker observation: UID/GID 57439, effective capabilities
zero, NNP enabled, root mount `ro` and denied write observed, temporary writes work,
118 CA roots, Kombu 5.6.2, nine Primer3 reference facts, 24 BLAST version checks,
synthetic exact match and timeout/exit classification successful. Exhaustive ELF
inspection still reports optional Tk/wish dependencies; direct inspection of wheel
internal libraries is distinguished from a contextual sibling-library check plus
actual native imports. Unresolved libraries remain failures.

Local candidate construction was interrupted by **host disk exhaustion and Docker
content-store I/O errors**. Only disposable DEPLOY-03 comparison archives were
removed after retaining hashes/reports; personal files and development containers
were preserved. [Interruption evidence](../../infra/hardening/evidence/local-arm64-interruption.json).
Native GitHub AMD64/ARM64 runners are the continuation path; no emulated result is
claimed. Docker Desktop observations concern its Linux VM, not host macOS kernel
isolation; native Linux execution is separately required.

## Dependency and provenance controls

Python runtime dependency closures were extracted from installed baseline package
metadata, including enabled extras and environment markers. Exact release versions
and published PyPI SHA256 hashes are retained under `infra/hardening/locks`.
`kombu==5.6.2` is unchanged. Installing with `--require-hashes` prevents an unpinned
transitive Celery resolution; this addresses the isolated DEP-1 experiment without
a broad dependency upgrade. A lock is not vulnerability acceptance.

Primer3 remains 2.6.1 with source SHA256
`805cef7ef39607cd40f0f5bb8b32e35e20007153a0a55131dd430ce644c8fb9e`.
Parameters and nine golden values are unchanged. BLAST remains 2.17.0. Official
archives were streamed without retaining or executing binaries; their upstream MD5
values matched. Captured SHA256 values now pin production downloads as well:
ARM64 `cb9ac252a1ac8767d90b0bf0a38486f3cb94f71ef9b6b8d194ded19b30250daf`,
AMD64 `3888112d8207831aa47371d93583c601f058f88b5db22dc782438b039a3a411b`.
[ARM64 proof](../../infra/hardening/evidence/blast-download-arm64.json),
[AMD64 proof](../../infra/hardening/evidence/blast-download-amd64.json).
These bind observed HTTPS archive bytes, not an upstream signature or attestation.

## Final native qualification

Code `7b9dca48fdf410014d24b060f49d77763f0d24d0` completed all functional and
scientific checks on native AMD64 and ARM64. Retained [final evidence and summary](../../infra/hardening/evidence/qualified-7b9dca4/summary.json)
binds results, actual installed Bio 1.88 / NumPy 2.5.4, manifests, digests and
architecture. The following handoff changes are documentation/evidence only.

| Check | AMD64 | ARM64 | Evidence |
|---|---|---|---|
| Mandatory make format/lint/typecheck/units | PASS | PASS | [Native regressions](https://github.com/El-Castor/OligoSpace/actions/runs/42807902881) |
| PostgreSQL and migration round-trip | PASS | PASS | Same native run |
| Chromium application journeys | 29 PASS | 29 PASS | Same native run, uploads-disabled overlay |
| Runtime controls, readiness, credential logs, clean stop/cleanup | PASS | PASS | Retained isolated-runtime.json reports |
| Real OIDC/permissions/revocation | 16 PASS | 16 PASS | [OIDC](https://github.com/El-Castor/OligoSpace/actions/runs/42807903128) |
| Scientific end-to-end, persistence/idempotency/CSV | 7 PASS | 7 PASS | [Scientific acceptance](https://github.com/El-Castor/OligoSpace/actions/runs/42807902751) |
| Primer3 nine values / BLAST / imports / ELF closure | PASS | PASS | [Exact OCI qualification](https://github.com/El-Castor/OligoSpace/actions/runs/42807903192) |
| Four S3 self/cross-restore contracts | 4 PASS | 4 PASS | API artifact storage reports, same OCI run |
| Standard application CI / bootstrap foundation | PASS | PASS | [CI](https://github.com/El-Castor/OligoSpace/actions/runs/42807902695), [foundation](https://github.com/El-Castor/OligoSpace/actions/runs/42807902930) |

Host controller checks also passed: 107 deployment, 26 hardening and 23
qualification-controller tests. Independent review and the targeted follow-ups
are complete, with no remaining critical/important code finding.

### Same-database final OCI comparison

[Final comparison](https://github.com/El-Castor/OligoSpace/actions/runs/42807903081)
uses pinned Trivy and one frozen DB SHA256
`eca36c960436a6ba904508098b151f7f2f70b6300e8b002aef587e816505dd11`,
updated `2026-11-10T10:23:24Z`, unchanged after offline scans on all four pairs.
All final scans completed with findings, all runtime probes passed, secrets zero.

| Artifact | Baseline OCI MiB | Final OCI MiB | Variation | Final C / H / M / L / U | Inventory |
|---|---:|---:|---:|---|---:|
| API AMD64 | 219.13 | 86.81 | -60.39% | 0 / 0 / 22 / 4 / 0 | 163 |
| API ARM64 | 175.85 | 85.02 | -51.65% | 0 / 0 / 22 / 4 / 0 | 163 |
| Worker AMD64 | 509.64 | 377.36 | -25.96% | 0 / 0 / 22 / 4 / 0 | 131 |
| Worker ARM64 | 414.80 | 324.00 | -21.89% | 0 / 0 / 22 / 4 / 0 | 131 |

The same final DB baseline remains 46 HIGH occurrences per image. Earlier
individual final-image scans reported API 11 MEDIUM / worker 12 MEDIUM; they used
an earlier DB and preceded the Bio update. The final common DB adds eleven MEDIUM
occurrences: seven util-linux `CVE-2026-76642` rows and four CPython
`CVE-2026-7210` rows. This dated coverage change is retained rather than concealed.
No fixed version is offered for the remaining findings in that final snapshot
scan. All finding rows, vendor scores, sources, packages and available fixes are
retained in the receipts; this table is not an advisory waiver.

`CVE-2026-76642` still has CVSS 7.8 (v3) / 8.5 (v4) and Noble needs-evaluation;
`CVE-2026-7210` has CVSS 7.5 and Noble needs-evaluation, with complete mitigation
requiring both CPython and Expat changes. Two GnuTLS findings retain vendor CVSS
7.4. These four high-scoring upstream IDs remain open even though Ubuntu/Trivy
priority is MEDIUM. No supported snapshot fix was demonstrated; unstable package
mixing, custom unsupported runtime substitution and global exemptions were rejected.
The upstream Biopython HIGH absent from Trivy was specifically fixed, not waived.

All-severity OCI gates therefore remain **FAILED**, as do relevant historical
DEPLOY-02/storage/source checks. A successful comparison job means completed
measurement, not scan acceptance. No gate, required check or finding was disabled.

## Still required before release or pilot acceptance

- Owner PR review and any separately authorized integration/publication decision.
- Resolution/review of residual and evaluation-pending advisories, including
  high-scoring CVSS discrepancies; no automatic risk acceptance.
- Object-provider license/provenance/visibility decision and historical MinIO
  availability resolution; no automatic SeaweedFS/Garage adoption.
- R1-08/R1-09 host/backup/TLS operations and R1-10/R1-11 curated-data/human acceptance.

Coverage limits remain explicit: package/SBOM presence is not exhaustive advisory
coverage, particularly for C libraries bundled inside Python wheels. Native ELF
closure proves resolution and execution, not absence of vulnerabilities. Vendor
`needs-evaluation`/`ignored` statuses remain open even when scanner findings are
absent. Locked inputs and documented build digests do not claim bit-for-bit equal
archives across timestamps or provenance envelopes. Standard Chromium qualification
uses the existing uploads-disabled, no-object-service overlay because the historical
MinIO image is unavailable; S3 SDK/cross-restore contracts are independently tested,
and no replacement provider is adopted. Golden fixtures do not replace validation
on owner-curated biological data or human R1-10/R1-11 acceptance.

Technical qualification, publication and authorization to operate are separate.
Every unresolved DEPLOY-02 security, SeaweedFS/Garage provenance/license/visibility
gate remains open. R1-10/R1-11 human acceptance and R1-08/R1-09 operational gates
are unaffected. DEPLOY-04 implementation remains unauthorized; recommendations below are preparatory only.

## Recommendations for a separately authorized DEPLOY-04

Review unresolved Ubuntu/source-package advisories against actual backports before
pilot acceptance; a lower vendor severity or missing advisory is not a fix. Keep
the ignored ACL issue and six evaluation-pending IDs visible. Review base digest
and snapshot together on new fixes, with native scientific/OIDC requalification;
the snapshot service promises bounded historical retention, not indefinite builds.

Resolve object-store supplier, license and provenance gates independently. Establish
registry/signing/publication authority separately from these local OCI receipts;
an unsigned SBOM/provenance projection is not a verified supplier attestation.
Then qualify the real authorized host, backup/restore and TLS/session operations,
plus owner-curated data and human scientific acceptance. No such action is started
by this PR.
