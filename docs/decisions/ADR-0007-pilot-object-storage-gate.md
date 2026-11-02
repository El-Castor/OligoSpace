# ADR-0007 — Open-source pilot object-storage qualification gate

- Status: **proposed provider choice / release blocked**.
- Date: 2026-11-01; requalified 2026-11-02. Workstreams DEPLOY-01/02.
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

## Targeted follow-up — no provider adoption

Controller44bb074 qualifies the explicit SeaweedFS4.52 digest variant on native
ARM64/AMD64: go-jose4.1.6 present, six self/cross restores pass. Its scans remain
blocked by3 UNKNOWN advisories and38 license observations per architecture;
upstream publication workflow failure and unverified signature trust are retained.
Default4.51 and pilot MinIO remain unchanged. Garage2.5.0 source CycloneDX SBOM
contains542 components; Cargo.lock scan has1 HIGH/3 MEDIUM/7 LOW. Exact OCI and
public release binaries match on both architectures, without establishing
source-to-binary attestation or complete runtime inventory. No clean-image claim.
See [consolidated targeted review (single PR18)](../deployment/DEPLOY_02_TARGETED_REVIEW.md)
and its retained evidence. Supplier choice and risk acceptance still require
user validation; PR18 remains DRAFT/unmerged.

## Application contract and evidence boundary

MinIO Python SDK 7.2.20, unchanged `ObjectStorage.put`: bucket existence/creation,
PUT stream/length/content-type. The attachment limit is 10 MiB. Checksums, access
scope and quarantine are PostgreSQL facts; uploads stay disabled by D2. GET/stat,
list and user metadata are additional qualification/recovery requirements, not
new application features. No claim of complete S3 coverage, versioning, retention
locks, replication, malware scanning or download publication is made.

Current evidence: tested code `98a3250339d2e17b59caff28061ac286f8549708`,
[native run41458888349](https://github.com/El-Castor/OligoSpace/actions/runs/41458888349),
[retained security reports](../../infra/deployment/evidence/security-98a3250-remediation.json).
Eight S3 scenarios pass: independent self-restores and both cross-provider
logical directions on native Linux ARM64 and AMD64. Typed diagnostics establish
that the old SeaweedFS failure was an access identifier logged by AWS bootstrap,
not a tracked secret-value match or log/controller failure. Official static
identity configuration removes that disclosure without weakening the gate.
See [corrective report](../deployment/DEPLOY_02_STORAGE_RELEASE_IMAGES.md) for
root causes and private non-root identity-file ownership correction.

Security remediation removes all reported application CRITICAL findings and final
secret alerts; web scans are clean, API/worker retain44 HIGH occurrences each
per architecture. Historical JWTs are public PyJWT documentation examples in pip
download cache, classified in RAM; cache is no longer shipped. Residual findings
remain blocking. Separate exact candidate scans now exist: SeaweedFS1 HIGH plus
3 UNKNOWN and license observations; Garage has no usable OS/Rust package inventory
and stays not_verified. Local Docker checks cannot access the socket; no host or
full-stack capacity qualification is claimed. See the complete
[security remediation matrix](../deployment/DEPLOY_02_SECURITY_REMEDIATION.md).


## Comparative matrix — 2026-11-02

| Dimension | SeaweedFS (priority1) | Garage (priority2) |
|---|---|---|
| Technical compatibility | Real unchanged adapter/SDK7.2.20 and all self/cross logical scenarios pass on both architectures; bytes/types/user metadata/SHA256 and refusal checked | Same contract and independent scenarios pass; region us-east-1, SDK-created bucket |
| Security | Strict log/port gates pass with official private static identities; exact image scan1 HIGH +3 UNKNOWN,274 packages/38 license observations; signature/dependency acceptance pending | Strict log/port gates pass, RUST_LOG=warn; exact scan has no OS/Rust inventory, coverage not_verified; no clean-image claim |
| Maintenance | Release4.51,2026-10-25, active release work[S3]; maintenance owner/security response SLA unqualified | Release2.5.0,2026-10-24, active releases[G3]; maintenance owner/security response SLA unqualified |
| Open-source license | Apache-2.0[S1]; no commercial license or activation required by tested community launch | AGPLv3[G1]; no commercial license/activation; retain notices and applicable redistribution/modified-network-service source obligations |
| Single-server suitability | Official mini combines services[S2]; no redundancy, representative load/durability qualification pending | SQLite metadata/objects, fsync; upstream single-node quick-start reserves this topology for testing without redundancy[G2,G5]; no unconditional pilot approval |
| Backup/restoration | Independent logical exports, self/cross imports and both restarts pass; coherent app/Keycloak/object off-host recovery pending | Same logical contract; internal disks are provider-specific and never reused across providers |
| ARM64/AMD64 resources | Both OCI descriptors and native Linux runs verified; observed samples roughly61–154MiB across this tiny corpus; not peak/VM/full-stack capacity | Both descriptors/native runs verified; roughly5–7MiB samples; same capacity limits |
| INRAE migration | Empty Linux target, new policy/credentials and logical checksum-verified import proposed, no actual cutover | Same logical path; AGPL obligations/topology and institutional review retained |

Snapshots are recorded per instance at two points only; allocated test-root disk
includes two instances plus exchange, excludes images/VM. Exact samples and disk
bytes are in retained reports. They do not qualify the real Apple Silicon16GB Mac
mini, historical ~66GiB free space, other users' preserved data or simultaneous
full development/pilot stacks. Native Linux ARM64 containers are not a Docker
Desktop/macOS validation. Neither source license alone certifies bundled layers.
Historical MinIO is compatibility-only (upstream maintenance stopped[M1]); AIStor
is excluded. Neither is silently reintroduced as a deployable alternative.

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
provisional: both synthetic storage contracts now pass, but Garage retains
a documented single-node production reserve and full capacity/security/backup
evidence remains incomplete. Application-image residual vulnerability gates remain
blocked; SeaweedFS has a candidate HIGH finding and Garage unresolved scanner
coverage. Candidate scan/provenance/license acceptance is still required. A passing Garage synthetic contract does not silently
switch the owner's priority or approve its pilot adoption.

Before final selection: address residual application/candidate vulnerabilities,
resolve Garage runtime inventory/provenance coverage, review dependency notices and
security maintenance, qualify representative capacity plus coherent off-host
recovery, assign maintenance/restore owners, then obtain explicit user approval.
The completed tiny synthetic contract does not waive those gates. The existing
MinIO-specific pilot entrypoint/environment is not a generic provider switch and
cannot simply receive a Garage/SeaweedFS image reference.

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
