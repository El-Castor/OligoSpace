# DEPLOY-04 — Verified backup and disaster recovery

Status: **backup/recovery technically qualified on isolated synthetic stacks**;
code review only, no pilot/release approval. Single [PR #22](https://github.com/El-Castor/OligoSpace/pull/22)
from main `ff3f629869d9d61a671c2ed94693a9d00d0c460c` after PR21 merge.
Qualified code: `953f5fbae2d24fa4be06ac8305f97ad1a31b44fa`.
Final documentation/evidence follow-up preserves the qualified controller/runtime tree.

## Architecture and targeted audit

Existing shell scripts cover an application-only unencrypted pg_dump and a
single-DB destructive development restore. Existing DEPLOY-02 S3 contracts cover
logical objects, not coordinated identity/application recovery. These utilities
remain explicitly development-only; no functioning component was reimplemented.

| Component | Delivered behavior |
|---|---|
| `infra/backup/recovery.py` | Pause/verify all writers, two native PG dumps, S3/configuration snapshot, resume verified; empty-target restore and interruption fence |
| `archive.py` | Private staged manifest with SHA256, streaming AES-256-GCM, authenticate before extraction, reject unsafe/missing/extra members, fsynced no-overwrite publication |
| `s3.py` | Current bucket/object keys, bytes, SHA256, sizes, content types, user metadata/tags; attachment references checked before mutation and after DB restore |
| `retention.py` | Authenticated external-filesystem transfer and configurable count/minimum-age cleanup; dry-run default, authenticate all points before opt-in deletion |
| `qualify.py` / native workflow | Real source/fresh-target/interrupted stacks, PostgreSQL-backed Keycloak, bounded API/worker/identity roles, OIDC/science/integrity/negative/secret tests |

Exact operator dependency hashes reuse DEPLOY-03; no application dependency,
scientific algorithm, Primer3 parameter or UI upload flow changes. Redis is fresh
transport, not restored authority. [ADR-0009](../decisions/ADR-0009-coordinated-logical-recovery.md)
records this bounded logical recovery choice and its revisit conditions.

## Point of consistency and manifest

Reserve exclusive maintenance access and exclude direct external DB/S3 writers.
Every Compose service must be listed: only explicitly identified DB/Redis/S3 can
remain up. Ingress/API/worker/scheduler/Keycloak are stopped and checked; no other
client session may remain on either database. Capture both databases and objects
inside this frozen interval, checking full table fingerprints and object indexes
again before completion. Resume only previously running writers in a finally
block and verify running/health state. Independent timestamps alone are not used
as a claim of global consistency; privileged external operators must respect the fence.

The encrypted manifest includes UTC, declared source SHA, PG versions, custom dump
TOCs, public-table row counts/SHA256, role attributes/memberships without password
verifiers, selected configuration, secret names and object/attachment inventories.
Native dumps preserve owners/ACLs, audits, identities, jobs/results and provenance.
All expected members/checksums and referenced objects are authenticated/checked
before import; restored rows and every object are read back. Same PG major and
matching preprovisioned role attributes/memberships are required. No migration,
role/password creation or automatic configuration installation occurs at restore.

Existing relations/functions/types/non-public schemas/extensions or nonempty buckets
are refused. An fsynced `restore-in-progress.json` prevents retry after interrupted
or failed mutation. Preserve the failed target for diagnosis and create another
empty target; no overwrite/drop/volume deletion override is available. Success
leaves writers stopped with `restore-verified.json`, pending controlled startup,
OIDC/permission checks and scientific reconciliation against fresh Redis.

## Commands, secrets and external destination

Use the [operator runbook](../BACKUP_RESTORE.md) for complete commands and protected
`configuration.example.json`: `recovery.py backup|restore --config ... --key-file ...
--archive ...`, then `retention.py transfer|prune` for approved external storage.
Python3.12, explicit local Unix Docker context, protected env/config/key files and
private state/staging are required. A realm JSON export is **not** the identity
backup: the whole Keycloak database is included.

No plaintext credentials, keys, realm dumps or archives are Git/CI artifacts.
Private plaintext staging requires an encrypted operator disk; SSD secure erasure
is not claimed. Keys, service credentials, TLS/session secrets and vault recovery
procedures remain outside Git, independently recoverable by authorized custodians.
Selected configuration is encrypted and never silently applied to a target.
Off-host destination setup and schedules are not installed. Destination filesystems
must support private Unix modes, hard links and fsync; unsupported semantics fail.

## Real restoration results and measured durations

[Native CI run](https://github.com/El-Castor/OligoSpace/actions/runs/42866007006):
**both AMD64 and ARM64 PASS**, with actual native CPU checks and no emulation.

| Platform | Complete backup | Integrity restore | Recovery / negative cases | Secret logs / retrievals |
|---|---:|---:|---|---|
| AMD64 native Linux | 27.944s | 14.218s | PASS / 11 | PASS / 21 |
| ARM64 native Linux | 26.042s | 13.065s | PASS / 11 | PASS / 21 |

Per platform:22 application tables compared,8 explicitly selected identity tables
(accounts/credentials/realm/clients/roles/scopes/mappers) compared independently,
and3 S3 objects (binary, Unicode/special key, empty). The core fingerprints **all**
identity public tables too. UUIDs, relationships, audits, scientific job/result
and provenance are preserved. A fresh OIDC login maps to the original subject;
reader mutations/jobs remain denied and a new Primer3 job succeeds after recovery.
Separate service-role SQL checks verify API DML and bounded worker grants, including
no worker deletion, oligo mutation or schema creation. No technical intervention
was needed to repair restored data.

- [AMD64 proof](../../infra/backup/evidence/native-amd64-953f5fb.json)
- [ARM64 proof](../../infra/backup/evidence/native-arm64-953f5fb.json)
- [Additional local ARM64 pass](../../infra/backup/evidence/local-arm64-e98276c.json)

These times measure a tiny synthetic corpus, not approved RPO/RTO, peak memory,
large-table throughput, total return-to-service or full16-GB pilot capacity.

| Negative case (both native architectures) | Observed result |
|---|---|
| Corrupt archive / truncated archive | Authentication/integrity refusal, target untouched |
| Wrong key / missing key | Refused, no target import |
| Missing identity dump | Completeness refusal before import |
| Missing object | Inner/outer integrity refusal before import |
| Object and its S3 entry omitted together | Preserved DB attachment reference detects omission before import |
| Function-only target / nonempty restored target | Refused without destructive cleanup |
| Interrupted after application DB import / retry | Identity remains empty, journal fences retry, writers remain stopped |

30 targeted backup tests pass, plus107 deployment,26 hardening and23 auth-controller
checks. [General CI](https://github.com/El-Castor/OligoSpace/actions/runs/42866006786),
[foundation](https://github.com/El-Castor/OligoSpace/actions/runs/42866006649),
[real OIDC](https://github.com/El-Castor/OligoSpace/actions/runs/42866007198),
[scientific acceptance](https://github.com/El-Castor/OligoSpace/actions/runs/42866006934)
and [native container comparison](https://github.com/El-Castor/OligoSpace/actions/runs/42866007085)
PASS at953f5fb. Native mandatory make/PostgreSQL/migrations/Chromium run
[42866006639](https://github.com/El-Castor/OligoSpace/actions/runs/42866006639)
**PASS** on both architectures, including mandatory make checks,206 PostgreSQL
cases/migrations and29 Chromium journeys per architecture. Only two redundant manual launches at the same
SHA were cancelled; corresponding automatic workflows ran all checks.

## Observed anomalies and independent review

[Independent review](../../infra/backup/evidence/independent-review.json) completed;
no remaining critical/important code finding observed. Four initial defects were
corrected: native ownership/ACL loss, relations-only empty checks, arbitrary writer
classification and attachment/object omission. Journals/publication are fsynced;
dumps and table fingerprints are streamed to bound host RAM.

Real execution additionally corrected disposable-only networking: internal bridges
cannot publish host ports, so only API/Keycloak/S3 attach to a loopback qualification
bridge; PG/Redis/workers stay internal. SeaweedFS advertised identity and API port
now match the isolated service. Host temporary parent remains private0700 even
where a child configuration must be readable by the container UID.

Garage emits its access identifier at WARN for unsupported GetObjectTagging501.
This is an **open supplier logging finding**, not suppressed or accepted. Its
[failed full recovery/log proof](../../infra/backup/evidence/garage-tagging-log-failure-arm64.json)
is retained. Final positive tests use previously qualified SeaweedFS4.52 at the
existing pinned digest, **strictly as a disposable service**; no pilot supplier
was selected or changed. Historical MinIO and any selected supplier need their own
full transfer/logging/maintenance/license qualification.

Fresh CI also refused unstable snapshot CA responses. Independent official HTTPS
endpoints returned the same140064-byte package and fixed SHA256. API/worker now
retrieve that unchanged CA package from archive.ubuntu.com; dated signed APT URIs,
CA version/hash, runtime/scientific pins and verification flags remain unchanged.
This necessary transport-only repair is documented in the
[equivalence receipt](../../infra/backup/evidence/ubuntu-ca-download-equivalence.json).

## Limits and remaining owner gates

- Current unversioned object namespace only; enabled/suspended version history,
  object lock and SSE are refused. Real nonempty tags and supplier bucket ACL,
  policy/lifecycle/replication behavior require additional supplier qualification;
  fixture user metadata and attachment checksums are exercised directly.
- Dedicated PG role inventory includes every non-system role; shared-cluster scope
  must be reviewed. Passwords and institution vault recovery are externally supplied,
  never proven by generated synthetic secrets alone.
- OIDC here uses an isolated HTTP test-only direct-grant client. Production/browser
  PKCE/TLS remain covered separately by existing OIDC/Chromium CI, not inferred here.
- External mounted-destination support and local transfer tests do not prove an
  actual off-host failure domain, institutional account or vault availability.
- Same PG major/identity release and exclusive maintenance are required. No PITR,
  WAL, online backup, cross-version migration or concurrent-operator guarantee.

Every DEPLOY-02/03 security/supplier/license/provenance gate remains blocking,
without waiver. R1-08 still requires approved off-host/vault procedures, capacity,
retention and measured owner-approved RPO/RTO. Daily full backups and periodic
isolated restores are proposals, not imposed objectives. R1-09 operations and
R1-10/R1-11 curated-data/human acceptance remain open. No Mac mini, real data,
Cloudflare, volume deletion, real migration, image publication, provider adoption,
merge or DEPLOY-05 was performed or authorized. Stop for owner code review.
