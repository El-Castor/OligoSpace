# DEPLOY-03 — Container hardening and security remediation

Status: **qualification in progress; not technically accepted** (2026-11-09).
Single branch `codex/deploy-03-container-hardening`, [PR #21](https://github.com/El-Castor/OligoSpace/pull/21),
from verified main `9ebbf2cd993395af2b154efb0b4cf5a76b4dd079`.
No production Dockerfile has been changed at this stage. No image publication,
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
| A | Original micromamba plus removal of development Python tooling | Same maintained trixie baseline; lower-layer bytes remain in OCI | Pending native comparison |
| B | Same `/opt/conda` prefix and scientific artifacts copied into pinned trixie-slim | Retains real Conda activation and metadata; ABI and optional-library closure must execute | Pending native comparison |
| C | Pinned official Python 3.12.16 slim-bookworm; hashed wheels; separate Primer3 builder | Maintained glibc distribution; Python patch change and all BLAST libraries require proof | Pending native comparison |

Recipes are experiments under `infra/hardening/strategies`, not production images.
Native CI compares all severities, full inventories, SBOM/provenance, final OCI
bytes, imports, dynamic libraries, CA trust, actual default entrypoint, non-root
read-only execution, nine Primer3 golden facts and a synthetic BLAST exact match.
No strategy is selected before those observations. Bookworm support ending before
trixie and inherited BLAST archive provenance remain explicit tradeoffs.

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
Parameters and nine golden values are unchanged. BLAST remains 2.17.0; upstream
MD5 sidecars are available, but an upstream-authenticated SHA256/signature has not
been demonstrated. Locally computing SHA256 will bind bytes without upgrading
their authentication claim. Additional checks remain pending.

## Remaining acceptance gates

- Complete native AMD64/ARM64 three-strategy builds/scans/SBOM/size/runtime table.
- Select only a demonstrated compatible and maintained strategy, then qualify its
  production/tooling consumers and version coherence.
- Run mandatory make checks, PostgreSQL/migrations, Chromium, native 16 OIDC and
  seven scientific journeys, Redis/Celery/idempotency and concerned S3 contracts.
- Complete start/stop, secret permissions, exposed-service, library and hardening
  proof on both architectures; retain all failure and residual-risk evidence.
- Finish independent review, correct findings and update tracking/memory/final CI.

Technical qualification, publication and authorization to operate are separate.
Every unresolved DEPLOY-02 security, SeaweedFS/Garage provenance/license/visibility
gate remains open. R1-10/R1-11 human acceptance and R1-08/R1-09 operational gates
are unaffected. DEPLOY-04 recommendations will follow the completed comparison;
DEPLOY-04 implementation is not authorized.
