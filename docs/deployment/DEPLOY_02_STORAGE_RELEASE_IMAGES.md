# DEPLOY-02 — Object Storage & Release Image Qualification

2026-11-01. Branch `codex/deploy-02-storage-release-images`, based on main
`75179a52da0d929922c904ff6df06d94eb7a1a67`: PR17 merged after exact approved
`8d0cd09a1294dcd2c6a504acc2bd3e842ff038ff`, 14 successful checks and no conflict.
Qualification only: no pilot deployment, real-object migration, registry image
publication or automatic merge of DEPLOY-02. Personal `assests/` is untouched.

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
Never attach a historical MinIO volume to AIStor or SeaweedFS. Any future migration
must export/import logically and reconcile database references, keys, bytes,
content-types and hashes, preserving originals until acceptance.

## 2. Candidates and evidence

Public manifest receipts, exact index/platform digests and inspection failures:
[`public-images-2026-11-01.json`](../../infra/deployment/evidence/public-images-2026-11-01.json).
Manifest availability proves neither a working runtime nor trusted signatures.

| Criterion | Historical MinIO | AIStor Free | SeaweedFS 4.51 |
|---|---|---|---|
| OCI availability | Public anonymous inspection 401; historical cache only | Public manifest inspected | Public manifest inspected |
| ARM64 | Historical DEPLOY-01 local run, not reverified now | Descriptor verified; execution blocked | Descriptor verified; execution unverified |
| AMD64 | Non verified | Descriptor verified; execution blocked | Descriptor verified; execution unverified |
| License | AGPL; redistribution review needed | Proprietary Free agreement; active license required | Apache-2.0 source license verified |
| Maintenance | Upstream states no longer maintained | Vendor distribution; Free has no SLA | Release 4.51 dated 2026-10-25; no project SLA established |
| MinIO SDK compatibility | Historical limited DEPLOY-01 evidence | Non verified | Non verified; synthetic runner prepared |
| Metadata preservation | Full suite non verified | Blocked | Non verified |
| Independent restore | Full suite non verified | Blocked | Non verified |
| RAM/disk | Current measurements unavailable | Unavailable | Unavailable |
| Migration risk | Archive/provenance/patch ownership unresolved | License and logical format migration unresolved | Logical migration and API edges unresolved |
| Operating cost | Internal security maintenance uncosted | No license fee does not imply no operating cost | Single-server maintenance/backup burden uncosted |
| Recommendation | Do not qualify as maintained release | Leave blocked by explicit user decision | Candidate for tests, not approved replacement |

### Historical artifact

Reference `minio/minio:RELEASE.2025-09-07T16-13-09Z`; historical cache digest
`sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`.
The source tag and local ARM64 observation recorded in DEPLOY-01 do not prove
current availability, AMD64 support, redistribution rights or maintenance.
[Upstream](https://github.com/minio/minio) is not a supported release guarantee.
An internal archive or source build would require explicit licensing, provenance,
patch ownership and cost acceptance; neither is authorized or implemented here.

### AIStor Free — explicit hold

The user chose **“Laisser AIStor bloqué pour cette PR”**. No agreement accepted,
account created, license requested, image downloaded or AIStor runtime executed.
Public metadata only: `quay.io/minio/aistor/minio:RELEASE.2026-09-19T17-05-25Z`,
index `sha256:107cf2014a9583c74c11e3cdbd6903d89c2244355886b89ce532f4ecae9c23f3`.
Both Linux platform descriptors exist; Docker Compose/SDK/restore/resource
compatibility remains unverified.

The [container guide](https://docs.min.io/aistor/installation/container/install/)
requires a license file passed with `--license`; its example is not a release pin.
The [Free agreement](https://www.min.io/legal/aistor-free-agreement) covers
research/educational use under commercial terms, with redistribution restrictions;
institutional acceptance is not inferred from technical suitability.
The [license documentation](https://docs.min.io/aistor/operations/licenses/)
describes single-node Free operation without SLA and paid-only capabilities
including encryption at rest and replication. Renewal/expiry, secrets handling,
recovery and security exceptions require review before reconsidering this hold.

### SeaweedFS — candidate C

[Release 4.51](https://github.com/seaweedfs/seaweedfs/releases/tag/4.51),
[Apache-2.0 license](https://github.com/seaweedfs/seaweedfs/blob/4.51/LICENSE),
[official usage](https://github.com/seaweedfs/seaweedfs/blob/4.51/README.md),
[S3 API documentation](https://github.com/seaweedfs/seaweedfs/wiki/Amazon-S3-API).
Image `chrislusf/seaweedfs@sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8`.
The disposable runner uses `mini -dir=/data` with explicit bind/name and generated
AWS credentials. Its internal services increase operational complexity; no ports
are published. A fresh independent data directory per instance is mandatory.
A recent release and documented S3 operations are evidence for investigation,
not production acceptance. No Compose pilot provider or storage format changes.

## 3. Synthetic qualification and actual results

`infra/deployment/s3_contract.py` and `qualify_storage.py` prepare three synthetic
binary objects with Unicode/special keys, SHA256, content-types and user metadata.
They test bucket creation, PUT/GET/stat/list, restart persistence, logical export,
restore into a second independently credentialed instance, target restart and
comparison. They check bad credentials, logs and absence of published ports.
Disposable directories/network/containers are uniquely identified; cleanup always
attempts generated credential removal, including when another cleanup fails.
No existing volume or user data is mounted. Logical exports are test-only and do
not constitute a coherent production database/identity/object backup.

**Runtime results: blocked locally.** Docker daemon is unavailable; it was not
restarted. Historical cached images and previous OCI exports were not assumed
available. SeaweedFS tests are prepared for disposable native CI runners; no
successful S3 runtime or cross-provider migration is claimed. AIStor is explicitly
blocked by user decision. No RAM/disk consumption measurement is available.
The real Mac mini has 16 GB RAM and historical ~66 GiB free, shared with other
users: two full stacks cannot be approved without actual capacity/margin checks.

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

The new PR workflow prepares six native jobs (three roles × ARM64/AMD64), verifies
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

Current status: **no fresh build, emulated run, native run, cross-architecture
comparison or release digest has been established for DEPLOY-02**. CI remains
pending until push/PR access succeeds. Never substitute DEPLOY-01 evidence for
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

- Local static suite: 21 tests passed using Python 3.12.2, including offline
  Compose resolution; Ruff 0.9.7 lint/format passed; `make compose-config` passed.
- Independent source review identified Linux exchange-directory ownership,
  exported-versus-loaded image binding and interrupted cleanup issues; fixes and
  negative tests are included. Runtime behavior remains unverified.
- Full application container checks, integration/E2E, builds, S3 scenarios,
  scans and native scientific comparison remain unverified here because Docker
  is unavailable. Existing suites are retained; no fresh pass is claimed.
- GitHub shell push/PR attempts timed out; until successful publication, no
  DEPLOY-02 PR number, CI run or green-check claim is available.

Open gates: authorized maintained storage decision; AIStor institutional/license
review (explicit hold); SDK/restore/cross-provider qualification; measured capacity;
native image builds and scientific comparison; complete scans and risk handling;
registry ownership/retention/trust; real OIDC/TLS/security gates and coherent
identity/database/object recovery from the pilot plan. No accepted deferral is
inferred. ADR-0007 stays proposed and the release stays blocked.

Recommendation: review the tooling separately from architecture acceptance;
qualify SeaweedFS synthetically when execution becomes available, retain the
AIStor hold, and ask the owner to select storage only after evidence review.
No provider, license, format, pilot deployment or registry publication is approved
by this report. DEPLOY-02 must remain draft and unmerged.
