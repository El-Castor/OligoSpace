# DEPLOY-02 — Object Storage & Release Image Qualification

2026-11-01. Branch `codex/deploy-02-storage-release-images`, based on main
`75179a52da0d929922c904ff6df06d94eb7a1a67`: PR17 merged after exact approved
`8d0cd09a1294dcd2c6a504acc2bd3e842ff038ff`, 14 successful checks and no conflict.
Qualification only: no pilot deployment, real-object migration, registry image
publication or automatic merge of DEPLOY-02. Personal `assests/` is untouched.

## Revised execution scope — user decision, 2026-11-01

The owner now requires open-source, no-fee storage without commercial licensing or
activation keys. SeaweedFS is priority 1, Garage priority 2; historical MinIO is a
compatibility reference only. AIStor is excluded from the architectural shortlist,
superseding the earlier pending-license hold retained in Git history. This authorizes tests,
not a final provider selection or pilot Compose substitution.

Execution: inspect pinned Garage/SeaweedFS sources and manifests; extend the
existing disposable contract to both providers and both logical cross-import
directions; generate isolated Compose definitions with persistent fresh data paths;
test refusal/configuration/backup safeguards locally; run real S3/resource/native
scenarios only on an available authorized container engine; update ADR-0007,
comparative evidence and memory, independent review, then draft PR without merge.
Key review cases: SDK-created bucket (not precreated), matching default region,
Garage metadata and data persistence, credential-free logs/config cleanup, failed
runtime evidence never promoted to a pass. Existing branch is retained as requested.

## 1. Application contract and preservation

The real adapter `apps/api/src/oligospace_api/services/object_storage.py` uses
MinIO SDK 7.2.20: `bucket_exists`, `make_bucket`, `put_object` with key, binary
stream, length and content-type. Endpoint, access/secret keys, secure transport
and bucket come from configuration. No application GET/download is implemented.
Checksums, ownership/visibility and quarantine are relational application facts,
not assumed S3 metadata. Production uploads remain disabled (D2); existing
attachment rows and objects must survive. This lot changes no application policy.

Qualification adds GET/stat/list and user metadata for logical backup/restore;
these are test/recovery requirements, not newly delivered user features. Object
versioning, tags, ACLs, replication, retention locks and multipart workflows are
not qualified. An S3-compatible endpoint never implies compatible internal disks.
Never attach a historical MinIO volume to Garage or SeaweedFS. Any future migration
must export/import logically and reconcile database references, keys, bytes,
content-types and hashes, preserving originals until acceptance.

## 2. Open-source candidates and current recommendation

The authoritative comparative matrix, all three platform digests per candidate,
source licenses, maintenance observations, migration implications and provisional
recommendation are in [ADR-0007](../decisions/ADR-0007-pilot-object-storage-gate.md).
The user-approved priority is **SeaweedFS, then Garage**. Neither provider has
been selected for the pilot. MinIO Community is compatibility-only; AIStor is
excluded from the architectural shortlist, not merely awaiting an activation key.
Earlier AIStor metadata is retained as history and is no longer queried by the
current inventory tool.

Fresh public manifest receipts:
[`public-open-source-images-2026-11-01.json`](../../infra/deployment/evidence/public-open-source-images-2026-11-01.json).
Both candidates have Linux ARM64 and AMD64 descriptors. SeaweedFS 4.51 is pinned
to `sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8`;
Garage 2.5.0 to `sha256:677e5b758e4425a325b811c425c026bf35a4bf42f7ddbaa773de3f4fd779a5a5`.
Public source/manifest inspection is not runtime, signature or scan qualification.

Source evidence supports community operation without activation/commercial
licensing: [SeaweedFS Apache-2.0](https://github.com/seaweedfs/seaweedfs/blob/4.51/LICENSE)
and [Garage AGPLv3](https://github.com/deuxfleurs-org/garage/blob/v2.5.0/LICENSE).
Credentials/RPC secrets still need protection; they are not activation keys.
Image dependency notices and SBOM/scans remain open. Recent releases demonstrate
activity, not a contractual security support SLA. AGPL redistribution/modified
network-service obligations must be retained for a future INRAE distribution.

For the single-host pilot, SeaweedFS remains the first qualification candidate.
Garage's [single-node guide](https://garagehq.deuxfleurs.fr/documentation/quick-start/)
explicitly excludes production use without redundancy; that reserve remains even
if all tests pass. Adding replicas on one Mac does not create failure independence.
No final architecture choice is inferred from candidate priority.

## 3. Synthetic qualification and actual results

`storage_profiles.py` prepares digest-pinned Compose services, each with new data
paths, its own generated credentials, no host ports and a unique internal test
network created/checked by the harness. Compose uses that network by explicit
name; it never attaches to an existing application network. Garage persists both
`/data/meta` and `/data/objects`, uses SQLite with fsync, a protected read-only
configuration, region `us-east-1` matching the unchanged SDK, and only bootstraps an
access key. The SDK must create the bucket. Default INFO bootstrap logs include
an access key, so the test explicitly sets `RUST_LOG=warn` and still checks both
log streams for every generated S3/RPC secret. No admin/web ports are enabled for
Garage's test configuration.

`qualify_storage.py` requires SDK 7.2.20. It first calls the unchanged application
`ObjectStorage.put` and reads persisted keys/bytes/content-types back through S3.
Then `s3_contract.py` adds user metadata and verifies SHA256 and binary/Unicode/
special-character keys, list/GET/stat, source restart, logical export, restore to
a second independently credentialed store, target restart, original preservation
and bad-credential denial. Restores verify all exported hashes before writing.
It records bounded engine/image architecture facts and labels native-container
execution separately from emulation/unknown status.

Prepared scenarios: SeaweedFS → SeaweedFS, Garage → Garage, SeaweedFS → Garage and
Garage → SeaweedFS. Native API CI jobs prepare all four sequentially on each Linux
architecture; no source volume is mounted into another provider. Clients run
with the host UID so private exchange files remain accessible on Linux. Cleanup
attempts every created container/network and removes generated credential/config
files even after another cleanup error. Temporary synthetic data is retained
outside Git for inspection; no Docker volume deletion is used.

Actual precheck receipts (both nonzero, no completed S3 check):

- [SeaweedFS runtime blocked](../../infra/deployment/evidence/seaweedfs-runtime-blocked-2026-11-01.json).
- [Garage runtime blocked](../../infra/deployment/evidence/garage-runtime-blocked-2026-11-01.json).

**Local runtime qualification remains blocked:** local `desktop-linux` Docker daemon
is unavailable. Initial GitHub shell requests timed out; branch publication
subsequently succeeded. No service was restarted.
Neither candidate's adapter/SDK scenario, persistence, restore or native runtime
passed locally; subsequent remote CI results are recorded below. There is no new MinIO runtime or real migration result.

RAM/disk: **not measured on the Mac mini**; Linux CI snapshots follow below. The runner records Docker memory snapshots after PUT
and after restore/restart, plus allocated temporary disk bytes. This small corpus
cannot prove peak working set, concurrency, backup disk headroom or whole-pilot
capacity. Compare on the same engine/architecture/corpus, include Docker VM and
other application services, then run a representative bounded workload before
accepting the 16 GB Mac mini. Historical ~66 GiB free is not current capacity;
other users' data must be preserved. Do not approve simultaneous complete dev and
pilot stacks without measurement. Compose resolution alone does not qualify
Docker Desktop file-sharing, fsync or macOS resources. Native Linux CI would not
constitute an actual Mac mini test.

Future INRAE migration is logical and provider-independent at the object contract:
empty approved Linux target, new credentials/policies, verified keys/types/metadata/
hashes, coherent relational/quarantine references, original retained and reversible
cutover after recovery acceptance. Neither byte-copying internal volumes nor using
an AMD64 manifest alone proves migration safety. No actual migration is authorized.

### Observed native CI results at 6a31dd5 (supersede local-only status above)

[Run 41343480403](https://github.com/El-Castor/OligoSpace/actions/runs/41343480403),
source `6a31dd5b19540879c0fa9cc72b7a718d1de6626c`; retained
[qualification summary](../../infra/deployment/evidence/ci-6a31dd5-qualification-summary.json).

| Scenario | ARM64 runner | AMD64 runner |
|---|---|---|
| Garage → independent Garage | Passed, including adapter, hashes/types/metadata, both restarts, denial, log/network checks and cleanup | Passed, same checks |
| SeaweedFS → independent SeaweedFS | Failed in final log/network/resource gate | Failed in same phase |
| SeaweedFS → Garage | Data/restore calls completed, overall final gate failed | Same |
| Garage → SeaweedFS | Data/restore calls completed, overall final gate failed | Same |

All failed reports retain `status=failed`; reaching the final phase is evidence of
prior synchronous data checks, not a complete qualification. The first report
suppresses the exact exception. Re-execution at `ddfd0c2`,
[run 41344277644](https://github.com/El-Castor/OligoSpace/actions/runs/41344277644),
[retained gates](../../infra/deployment/evidence/ci-ddfd0c2-storage-gates.json),
identifies `secret_log_gate` in all six SeaweedFS-involving cases and confirms
Garage self-restore passes on both architectures. The check includes access-key
identifiers and secret values and also refuses log-read failures; this is not yet
a finding that a secret value specifically was leaked. Diagnose that distinction
before accepting or changing logging configuration. No raw server
log or credential value is uploaded. No provider is approved from these results.

Actual Docker snapshots: Garage ~5–7 MiB, SeaweedFS ~59–76 MiB (partial after-PUT
samples). Garage test-root allocation totals 4,423,680 bytes on ARM64 and
4,456,448 bytes on AMD64, including two stores plus logical exchange/config; this
excludes images/engine and is not a per-instance footprint. SeaweedFS disk/final
measurements were not reached. These are tiny synthetic workloads on independent
Linux runners (~16 GB RAM/4 CPUs), not measurements of the Mac mini or peak load.

All six role/architecture OCI structures validate. Both real Primer3 runs use
2.6.1 and identical inputs/parameters: nine compared numeric facts have maximum
absolute difference 0.0 (allowed 1e-6). Manual aggregation of retained reports
passes while explicitly keeping `release=blocked`; the automatic aggregate job
was skipped because its dependencies failed. Four scan reports fail execution
with categories `archive`, `manifest`, `oci`; API scans were not reached after S3
failure. No vulnerability acceptance is inferred. Existing application CI and
deployment-contract jobs passed at this SHA; no fresh E2E run is claimed.

## 4. Image construction and supply-chain checks

API/migration and worker/scheduler retain shared role images. Dockerfiles pin
Micromamba 2.4.0 and Node 22.23.0-alpine3.23 by public index digest. PostgreSQL,
Redis, Keycloak and Caddy manifests are inventoried without changing live services.
Release references must be digests, never `latest`; dependency updates require a
new review and scan, not silent repinning.

`build_local.py` exports only committed source from a controlled Git tree, records
full revision/platform, produces SPDX SBOM and SLSA provenance using a pinned
scanner, and refuses remote builders/endpoint overrides. `oci.py` validates OCI
archive paths, reachable blob bytes/digests, platform, nonroot configuration,
revision and subject-bound attestations. Attestations are not cryptographically
trusted signatures; uncompressed layer semantics and arbitrary embedded secrets
are not exhaustively proven by this structural validator. A loaded test image must
match the exported configuration digest and rootfs identities.

`scan_artifact.py` prepares actual pinned Trivy vulnerability/secret scanning of
the OCI archive. Raw matches stay temporary; only sanitized counts/CVE IDs,
archive checksum and available database metadata are retained. Findings fail the
release gate even when collection succeeds. **No scan ran locally; no vulnerability
cleanliness or exception acceptance is claimed.** Scanner execution and complete
report/database evidence must be inspected before any release decision.

## 5. Architectures and scientific evidence

Draft [PR18](https://github.com/El-Castor/OligoSpace/pull/18) runs six native jobs (three roles × ARM64/AMD64), verifies
runner CPU, exports OCI and runs worker tests plus unchanged real Primer3 analysis.
Public [GitHub runner documentation](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
provides native `ubuntu-24.04` and `ubuntu-24.04-arm` runners; workflow availability
is not evidence that this branch has run there.

`science_probe.py` records identical inputs, salt/DNA/model parameters, tool
version, units and computed payload. `collect_reports.py` requires matching
source/tool/input/parameter evidence and compares finite numeric results with
absolute tolerance 1e-6, relative tolerance zero; it reports each delta. No change
to Primer3/scientific rules is made. Aggregation produces offline OCI indexes
binding both role manifests. They are not published/pullable multiarch releases.

First draft PR CI at `23b99d7` (run `41342999866`) produced API native build and
structurally verified OCI evidence, including ARM64 revision/platform/SBOM/
provenance. Its scan execution failed without a detailed safe diagnostic, so S3
and science steps after it were not executed. This is not scan acceptance or
runtime storage qualification. The workflow now runs independent SDK/science
checks before the scan and retains fixed error categories, never raw diagnostics;
scan failure still fails the job. New-revision native results remain pending. Never substitute DEPLOY-01 evidence for
this revision. Images/archives are not uploaded as public Actions artifacts;
sanitary evidence reports only have seven-day retention.

## 6. GHCR proposal — dry run only

`ghcr_plan.py` and manual `ghcr-dry-run.yml` calculate names under
`ghcr.io/el-castor/oligospace/{api,web,worker}:sha-<full-sha>` without login,
packages creation or publication. Actions permission is `contents: read`; no
`packages: write` or identity-token permission is granted.

[GHCR documentation](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry)
describes granular access, private initial packages and future authenticated
publication. Repository access does not establish package policy or permission.
Before authorization: decide visibility/readers, minimum token scopes, retention,
revocation and restore after artifact loss, signature trust, vulnerability policy
and immutable deployment digests. Tags remain mutable. Public downloads cannot
be recalled by later revocation. No historical MinIO image is republished.

## 7. Validation, review and remaining gates

- Local static suite: 29 tests passed using Python 3.12.2, including both
  candidate Compose resolutions and unavailable-engine fail-closed evidence;
  Ruff 0.9.7 lint/format and `make compose-config` pass. The required combined
  `make format lint typecheck test PYTHON_RUNNER=container` attempt fails at its
  Docker tooling-build prerequisite; those application checks did not run.
- Independent source review identified Linux exchange-directory ownership,
  exported-versus-loaded image binding and interrupted cleanup issues; fixes and
  negative tests are included. A new independent review found premature passed
  status on late measurement/cleanup failure; both cases were reproduced failing,
  corrected and verified passing. Runtime behavior remains unverified.
- Local application/container checks remain blocked by Docker. Remote CI evidence
  above establishes builds, application/integration checks and scientific comparison
  at its exact SHA, plus Garage self-restore. SeaweedFS gates, scans and full pilot
  qualification remain open; no fresh E2E success is claimed.
- Initial GitHub shell requests timed out; branch publication subsequently
  succeeded. Draft PR CI is pending; no native/runtime/scan success is claimed
  until its exact-head reports have been inspected.

Open gates: final owner selection of qualified open-source storage;
SDK/restore/cross-provider qualification; measured capacity;
native image builds and scientific comparison; complete scans and risk handling;
registry ownership/retention/trust; real OIDC/TLS/security gates and coherent
identity/database/object recovery from the pilot plan. No accepted deferral is
inferred. ADR-0007 stays proposed and the release stays blocked.

Recommendation: review the tooling separately from architecture acceptance;
qualify SeaweedFS first and Garage second on the same synthetic contract when
execution becomes available; AIStor is excluded. Ask the owner to select storage
only after evidence review.
No provider, license, format, pilot deployment or registry publication is approved
by this report. DEPLOY-02 must remain draft and unmerged.
