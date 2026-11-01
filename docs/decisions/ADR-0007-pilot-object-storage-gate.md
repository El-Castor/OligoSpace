# ADR-0007 — Pilot object-storage artifact and maintenance gate

- Status: **proposed / decision blocked**, not an accepted provider replacement.
- Date: 2026-11-01. Workstreams DEPLOY-01/02, following approved PR16 plan.

## DEPLOY-02 qualification update

The user explicitly chose **leave AIStor blocked for this PR**. No license is
requested, agreement accepted, account created, image downloaded or AIStor runtime
executed. Public manifest inspection establishes ARM64/AMD64 descriptors, not
license eligibility or application compatibility. Free-edition licensing,
single-node scope, missing SLA and paid-only encryption/replication require a
separate institutional decision. This supersedes any assumption that AIStor
qualification can proceed automatically.

SeaweedFS 4.51 is an additional candidate, not an approved replacement. Public
source/license and both platform manifests were inspected. Synthetic independent
S3-instance tests are prepared, but runtime qualification remains unverified while
the local Docker daemon is unavailable. Historical MinIO cache observations below
belong to DEPLOY-01 and have not been re-established in this session.

See [DEPLOY-02 evidence and limitations](../deployment/DEPLOY_02_STORAGE_RELEASE_IMAGES.md).
The proposed decision below remains unchanged: no provider substitution and no
ready release until the owner accepts a qualified option.

## Context and evidence

The existing application uses MinIO Python SDK 7.2.20, bucket existence/creation
and object PUT with key, bytes, content-type. Attachment rows retain checksum and
quarantine state. Uploads remain disabled in production; historical objects must
survive. S3 compatibility never proves internal-volume compatibility.

Source and public registry observations are recorded in PILOT_HOSTING_PLAN.md §5.
The [upstream repository](https://github.com/minio/minio) states it is no longer
maintained. The source tag exists; publicly readable image manifests were not
established (404/401 are not proof of universal absence). User reports that the
first Mac mini image download failed; no Mac mini was contacted for this work.

Local development cache contains the exact historical reference, ARM64, digest
`minio/minio@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e`.
This is evidence of a local artifact only, not a retrievable authorized release
registry, upstream support, AMD64 manifest or production maintenance guarantee.

## Options and consequences

| Option | Verified basis | Outstanding qualification / consequences |
|---|---|---|
| Same MinIO artifact retained in an authorized archive | Local ARM64 artifact and historical source exist | Provenance/license review (AGPL), registry authorization/availability, scans, all target platforms and an explicit maintenance owner; no such supported archive approved |
| Controlled build of pinned MinIO source | Source commit identified in the plan | Own supply chain and patch responsibility, locked base/dependencies, AGPL review, native tests and restore. Historical Dockerfile inherits latest, so is not a ready reproducible solution |
| MinIO AIStor | [Official offering](https://www.min.io/product/aistor) exists | Different distribution/licensing/support decision, ARM64 eligibility/digests/cost and object migration/restore compatibility not established; requires explicit approval |
| Another S3 implementation/service | No candidate qualified by this lot | Architecture/provider/data-governance decision, SDK edge cases and export/import migration qualification required; not an implicit fallback |

## Proposed decision

**Keep storage blocked rather than substitute.** Supply only a required
`MINIO_IMAGE` digest parameter in the independent definition, with MinIO-specific
command and environment contract. It is not a generic provider switch. No default
`latest`, mirror, silent image substitution or object-format conversion.

Before acceptance: choose a maintenance strategy with the owner, verify the
authorized registry and manifests/digests per architecture, license, scans,
bucket/object metadata/content-type/checksums, preservation across restart and
logical backup/restore. Any substantial change of supplier/license/maintenance
must receive explicit user approval before integration. Lack of a qualified option
blocks a ready pilot release; isolated core tests can continue.

Revisit when a supported, legally acceptable artifact plus maintenance and restore
evidence are supplied. No existing object, endpoint or volume is changed here.
