# ADR-0007 — Open-source pilot object-storage qualification gate

- Status: **proposed provider choice / release blocked**.
- Date: 2026-11-01. Workstreams DEPLOY-01/02.
- Owner decision accepted: open-source-only eligibility and candidate priority.
  No final provider selection, pilot substitution or real migration is accepted.

## User decision and supersession

Storage must be fully open source, free of charge, actively maintained and require
neither a commercial license nor an activation key. **SeaweedFS is priority 1,
Garage (Deuxfleurs) priority 2; historical MinIO Community is compatibility-only.**
AIStor Free is excluded because its commercial license does not meet this choice.
This supersedes its earlier priority and the interim “leave AIStor blocked for
this PR” hold; its public metadata receipt remains historical evidence only.
No licensing/account/download/runtime action is pursued for AIStor.

The former MinIO archive/source-build options remain historical analysis, not
recommended maintained pilot options under this directive. Existing Compose still
uses its original MinIO contract; no provider is silently substituted.

## Application contract and evidence boundary

MinIO Python SDK 7.2.20, unchanged `ObjectStorage.put`: bucket existence/creation,
PUT stream/length/content-type. The attachment limit is 10 MiB. Checksums, access
scope and quarantine are PostgreSQL facts; uploads stay disabled by D2. GET/stat,
list and user metadata are additional qualification/recovery requirements, not
new application features. No claim of complete S3 coverage, versioning, retention
locks, replication, malware scanning or download publication is made.

Current receipts and runtime blockers are retained under
[`infra/deployment/evidence`](../../infra/deployment/evidence/).
Docker local engine is unavailable and was not restarted. Both candidate
prechecks returned nonzero, `status=blocked`, `stage=engine_availability`, no
completed checks and `application_adapter_exercised=false`. No RAM, disk, S3 or
native runtime success can be inferred from manifests or unit tests.

## Comparative matrix — 2026-11-01

| Criterion | SeaweedFS (priority 1) | Garage (priority 2) | Historical MinIO reference |
|---|---|---|---|
| Source license | Apache-2.0, tagged source verified [S1] | AGPLv3, tagged source verified [G1] | AGPL; not a maintained target |
| Commercial license / activation | None required by the selected community source/launch contract [S1,S2] | None required by source/launch contract; RPC/S3 secrets are credentials, not activation [G1,G2] | No new licensing action; compatibility-only |
| Maintenance evidence | Release 4.51, 2026-10-25; active release work [S3] | Release 2.5.0, 2026-10-24; earlier 2.4.1 in September [G3] | Upstream no longer maintained [M1] |
| OCI source and version | `chrislusf/seaweedfs:4.51`, publicly inspected | `dxflrs/garage:v2.5.0`, publicly inspected | Historical tag; anonymous inspection blocked 401 |
| ARM64 / AMD64 | Both Linux descriptors verified; execution unverified | Both Linux descriptors verified; execution unverified | Historical ARM64 DEPLOY-01 only; AMD64 unverified |
| Current SDK operations | Documented S3; real adapter and recovery tests prepared; runtime blocked | Required S3 endpoints documented [G4]; real adapter tests prepared; runtime blocked | Limited historical DEPLOY-01 proof, not replayed |
| Single-host Compose | `mini` combines services; fresh `/data` bind and private network [S2] | Single-node SQLite config, `/data/meta` and `/data/objects`, private network; upstream reserves this mode for tests [G2,G5] | Existing definition unchanged |
| Region/bootstrap | SDK creates bucket; no precreated test bucket | `us-east-1` matches unchanged SDK; default key may create buckets; no default bucket [G6] | Existing SDK contract |
| Metadata / content-types / SHA256 | Test prepared, blocked | Test prepared, blocked | Full new suite unverified |
| Restart / independent logical restore | Test prepared, blocked | Test prepared, blocked | Historical limited test only |
| Cross-provider migration | Both synthetic export/import directions prepared, blocked | Same; never reuse another provider's volume format | Real export/migration prohibited |
| RAM and allocated disk | No measurement; two snapshot collection points prepared | No measurement; same corpus and snapshot scope | Current cache/resource use unverified |
| 16 GB Mac mini / ~66 GiB historical free | Capacity not accepted; Docker VM plus full app must be measured | Same; no single-node redundancy or production suitability inferred | No inspection of actual Mac mini |
| Linux AMD64 / INRAE | Descriptor available; native test and institutional acceptance pending | Descriptor available; same; multi-node recommendation adds topology/ops work | No maintained future target recommended |
| Operating obligations | Preserve notices; patch/scans, monitoring, backup and off-host restore owner needed | Preserve AGPL notices/source obligations for redistribution or modified network service; same operational work | No internal maintenance ownership approved |
| Recommendation | First qualification candidate; conditional pilot recommendation only | Keep second; explicit upstream single-node warning weighs against this pilot | Compatibility reference only |

Recent releases establish activity, not a security support SLA. Neither candidate
has a paid dependency in this proposed test contract. Bundled dependency notices,
SBOM/scans, provenance and maintenance ownership still need review; the source
license alone is not certification of every image layer.

## Immutable OCI observations

SeaweedFS index:
`sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8`.
ARM64: `sha256:7e68a388de0806ed8d96f30cb7e927182a3d80d42920cb87d97d23311a7a1a77`.
AMD64: `sha256:3a522c379599e163433a636e75022630848b63a74f08ea37bf06f8d776e9a707`.

Garage index:
`sha256:677e5b758e4425a325b811c425c026bf35a4bf42f7ddbaa773de3f4fd779a5a5`.
ARM64: `sha256:32b5de84cf9e3ae9c0b4d0f02566c442029e62203a4ed1bca9cdf2327fc19388`.
AMD64: `sha256:23b16d34e0348d9aca9b960a7429a7e6d494974b5288bfb8f6c3ab856895f71e`.

Manifest bytes were hashed during anonymous registry inspection. Platform
presence is not image execution, signature trust, scanner acceptance or a Mac
Docker Desktop qualification. Historical MinIO cached ARM64 digest remains
`sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`;
current cache availability is not established.

## Proposed recommendation and acceptance conditions

Continue **SeaweedFS first**, because its community license and single-server
entry point fit the owner's constraints with fewer licensing/topology burdens.
Keep Garage as a serious alternative but do not ignore its upstream warning:
one-node test success cannot approve a production pilot. Three containers on the
same Mac do not create independent failure domains. This recommendation is
provisional while runtime, capacity, restore and security evidence is missing.

Before final selection: run identical SDK and real adapter scenarios on independent
instances, validate all persisted bytes/types/metadata/hashes after restarts and
logical restore, run cross-import tests, collect dated native ARM64/AMD64 evidence
and resource measurements, scan exact artifacts, assign maintenance/restore owners
and have the user approve the comparative result. The current MinIO-specific pilot
entrypoint/environment is not a generic provider switch and cannot simply receive
a Garage/SeaweedFS image reference.

For future INRAE migration, use independent empty target volumes and approved
Linux images, rebuild credentials/bucket policy, transfer a checksum-verified
logical export, reconcile attachment keys/checksums/quarantine/permissions with a
coherent app/identity snapshot, and test recovery before opening access. Retain
the source unchanged until acceptance. Versioned metadata formats are provider-
specific; no direct internal disk reuse or architecture portability is assumed.
This is a procedure proposal, not authorization to execute a migration.

The storage/release gate remains blocked. No Mac mini/Cloudflare operation,
provider replacement, real-data transfer or automatic DEPLOY-02 merge is authorized.

## Sources (primary)

- S1: [SeaweedFS 4.51 license](https://github.com/seaweedfs/seaweedfs/blob/4.51/LICENSE).
- S2: [Tagged community usage](https://github.com/seaweedfs/seaweedfs/blob/4.51/README.md), [mini source](https://github.com/seaweedfs/seaweedfs/blob/4.51/weed/command/mini.go).
- S3: [SeaweedFS 4.51 release](https://github.com/seaweedfs/seaweedfs/releases/tag/4.51).
- G1: [Garage 2.5.0 license](https://github.com/deuxfleurs-org/garage/blob/v2.5.0/LICENSE).
- G2: [Quick start](https://garagehq.deuxfleurs.fr/documentation/quick-start/).
- G3: [Official release listing](https://garagehq.deuxfleurs.fr/_releases.html).
- G4: [Tagged S3 compatibility](https://github.com/deuxfleurs-org/garage/blob/v2.5.0/doc/book/reference-manual/s3-compatibility.md).
- G5: [Configuration and replication](https://garagehq.deuxfleurs.fr/documentation/reference-manual/configuration/).
- G6: [Tagged bootstrap source](https://github.com/deuxfleurs-org/garage/blob/v2.5.0/src/garage/server.rs).
- M1: [MinIO upstream status](https://github.com/minio/minio).

Implementation, execution receipts and remaining release gates:
[DEPLOY-02 report](../deployment/DEPLOY_02_STORAGE_RELEASE_IMAGES.md).
