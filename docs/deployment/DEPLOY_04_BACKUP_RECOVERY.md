# DEPLOY-04 — Backup and disaster recovery

Status: implementation under qualification in [PR #22](https://github.com/El-Castor/OligoSpace/pull/22).
Base `ff3f629869d9d61a671c2ed94693a9d00d0c460c`, after PR21 merge.
This lot authorizes disposable synthetic qualification only. No pilot, real data,
Mac mini, Cloudflare, image publication, provider adoption or real migration.

## Targeted audit and implementation

Previous scripts cover an unencrypted application-only pg_dump and destructive
single-DB test restore; DEPLOY-02 S3 tests cover logical objects only. They remain
explicit development utilities. No complete coordinated recovery existed.

`infra/backup/recovery.py` coordinates native logical dumps of application and
Keycloak databases, S3 export/import and verification. `archive.py` authenticates
the complete manifest/payload using AES-256-GCM; `s3.py` preserves current keys,
bytes, SHA256, size, content type, user metadata and tags without disk-format
coupling. `retention.py` provides authenticated transfer to an explicit mounted
external destination and opt-in age/count pruning. Exact operator dependencies
reuse DEPLOY-03 hashes. No new application dependency or framework.

## Consistency and integrity

An explicit exclusive maintenance window excludes direct external writers. Every
Compose service is accounted for; only the identified DB/Redis/S3 may remain up.
Ingress/application/worker/scheduler/Keycloak writers are stopped and checked,
then no remaining DB client is allowed. Both databases and objects are captured
inside this frozen interval, with repeat full-table/object-index checks.
Previously running source services resume in a finally block and must be healthy.
This is coordinated downtime, not online three-timestamp consistency.

The encrypted manifest includes UTC/source/release, PG versions, native TOCs,
all public-table row counts and SHA256, non-secret role attributes/memberships,
configuration allow-list, secret names, object inventory and attachment references.
Exact manifest members and SHA256 are authenticated before target mutation;
objects referenced by attachments must exist and match bytes/size/type. Native
restore preserves ownership/grants; target roles/credentials are preprovisioned
separately and attributes/memberships must match. Restored rows and all object
bytes/metadata are read back. No schema migration is performed by recovery.

Restoration requires all writers stopped and empty databases/buckets. Existing
relations/functions/types/non-public schemas/extensions are refused. An fsynced
journal fences interrupted/failed targets; no overwrite/drop/automatic retry or
automatic restart is available. Redis is fresh transport: DB-authoritative jobs
are reconciled by the existing scheduler, not replayed from an obsolete queue.

## Commands and secret recovery

See [the operator runbook](../BACKUP_RESTORE.md) for protected configuration,
key generation/escrow, backup, empty-target restore, verified copy and retention.
No secret/environment inspection output is uploaded. Plaintext staging is private
and transient; the operator disk must itself be encrypted (SSD secure erasure is
not claimed). Keep recovery keys separately in an approved encrypted vault with
independent custodians and test that recovery path. Configurations are inventoried
and encrypted, never automatically installed into a real stack.

## Qualification and review

Native workflow `.github/workflows/deploy04-recovery.yml` creates source, fresh
restore and interrupted-restore stacks with unique volumes. Synthetic data include
users/subjects, projects/targets/oligos/assays/experiment attachments, audits and
completed Primer3 jobs. API, worker and Keycloak use distinct database roles.
A fresh OIDC login, reader denials and a new scientific job are checked after
restoration. Database fingerprints include all public tables before services start.

Negative cases include corrupt/truncated archive, wrong/missing key, missing
identity dump, missing object, object-plus-manifest omission, function-only/nonempty
target and interruption after the first database. Failed integrity must never
start writers or report success. Logs are retrieved from both streams; retrieval
failure itself fails the secret gate. Archive/key/raw realm/DB contents are not
CI artifacts. Only bounded sanitized JSON evidence is retained.

Independent review identified and corrected four important issues before delivery:
loss of PG ownership/ACL, relations-only empty checks, arbitrary nonwriter
classification and attachment/object omissions. Additional improvements fsync the
journal/archive directories and stream dumps/table fingerprints to bound host RAM.
Final code review found no further critical/important finding; runtime acceptance remains separate.
Runtime qualification also exposed a harness port issue: Docker internal bridges do not
publish host ports. An additional loopback-only qualification bridge now attaches
only API/Keycloak/S3; PostgreSQL/Redis/workers remain on the internal network.
The temporary host root is private0700 even when a child file must be readable
by the disposable Keycloak UID. No production networking or image changed.

## Coverage limits and operational gates

- Qualification uses a tiny synthetic corpus; durations measure this workload only,
  not approved RPO/RTO, peak disk/RAM, full 16-GB pilot capacity or large tables.
- Garage is an isolated compatible test endpoint only. Historical MinIO availability,
  maintenance/license and transferability to the actual supplier remain open.
- Current unversioned buckets only; enabled/suspended version history, object lock
  and SSE are refused. Bucket policies/ACL/lifecycle/replication need external
  inventory/recreation; no provider-internal disk restore is claimed.
- Fresh OIDC here uses an isolated HTTP test-only direct-grant client; production
  PKCE/browser/TLS coverage remains in existing OIDC/Chromium CI, not inferred.
- Role passwords/Keycloak client secrets/TLS/session keys must be recovered from
  the separate vault. The qualification uses generated synthetic values, never
  exercises a real institutional vault or external failure domain.
- External destination support and local copy tests do not prove an actual off-host
  mount, account or institutional transfer. No schedules or network paths installed.
- Operator must enforce exclusive access and serialize operators; stopping Compose
  services alone cannot fence an independent privileged DB/S3 administrator.
- PostgreSQL major and identity release must match; cross-version/PITR/WAL/schema
  migration and fully automatic install/update are outside this logical pilot path.

DEPLOY-02/03 security/supplier/license/provenance gates remain blocking, without
suppression or waiver. R1-08 requires approved off-host/vault procedures and measured
owner-approved RPO/RTO; R1-09 operations and R1-10/R1-11 human acceptance remain open.
Suggested daily full maintenance backup and periodic restore are discussion inputs,
not imposed service objectives. Stop after PR review; no DEPLOY-05 or auto-merge.

## Evidence and measured durations

First real ARM64 run at source `482f6b6` verified the complete recovery path:
backup24.074s, restore11.523s,22 application tables,8 explicit identity-table
comparisons (core fingerprints all identity public tables),3 objects, fresh OIDC,
reader denials and a new Primer3 job. All11 negative cases passed. However the
final generated-secret log gate failed, so overall qualification remains FAILED
until corrected and replayed. See sanitized
[`correctness-before-log-fix-arm64.json`](../../infra/backup/evidence/correctness-before-log-fix-arm64.json).
These timings are observations on a tiny synthetic corpus, not accepted RPO/RTO.
Initial CI builds additionally encountered official Ubuntu500/502/503 and a
checksum-refused response; independent downloads confirmed the locked CA hash.
Neither hashes nor signature verification were relaxed. Final CI evidence pending.

## Observed provider logging defect

The Garage disposable service logs the S3 access identifier at WARN when the
backup SDK requests unsupported `GetObjectTagging` (HTTP501). The private
reproduction classified the service/credential label without retaining any
credential value. This remains an open supplier logging finding, not accepted or
silenced. The final qualification therefore also uses the previously tested
SeaweedFS candidate strictly as an isolated synthetic S3 service, not as a pilot
provider decision. The same full log gate, tags/metadata/checksum and permission
checks remain active. Historical MinIO and any actual chosen provider still need
its own complete transfer/logging/maintenance/license qualification.
