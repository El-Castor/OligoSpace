# Backup and restore

DEPLOY-04 provides coordinated logical recovery tooling; it does **not** authorize
an installation, real data access or a pilot. See the [qualification report](deployment/DEPLOY_04_BACKUP_RECOVERY.md).
The legacy `create-backup.sh`, `restore-test.sh` and `make backup` remain single-DB
development utilities, **not full recovery commands**. The legacy restore drops its
explicit test database; the new path never drops a database or deletes a volume.

## Operator preparation

Use Python 3.12 and an isolated venv, Docker Compose v2 and the exact source release:

```sh
python3.12 -m venv /absolute/private/recovery-venv
/absolute/private/recovery-venv/bin/pip install --require-hashes -r infra/backup/requirements.txt
```

Copy `infra/backup/configuration.example.json` outside Git; replace placeholders
from an authorized secret manager and `chmod 600` the config and runtime env file.
The file contains credentials: never print it, upload it or use shell tracing.
Use an explicit local Unix Docker context; remote engines and inherited overrides
are refused. The Compose file is explicit and may not be a symlink. The protected
state directory must be unique to the target project and preserved across retries.
List every service: only the explicitly identified PostgreSQL/Redis/S3 services
may remain running. All others belong in `writers`, including ingress, Keycloak,
API, worker and scheduler. Protected configs must be owned by the operator.

Inventory separately, outside Git: image digests/release source, Compose definition,
Keycloak realm/hostname/client configuration, TLS trust/certificates, database names,
role names/attributes/memberships/privileges, S3 bucket policy/region/quarantine
settings, Redis/worker reconciliation settings, DNS and external routing needs.
`configuration_files` is an explicit allow-list, embedded encrypted and never
automatically installed at restore. `secret_inventory` contains uppercase names
only. Preserve actual database/OIDC/S3 credentials, NextAuth/session keys, private
TLS keys and backup keys **separately**, encrypted in an approved vault with a
second authorized recovery custodian. Test recovery of that vault independently.
A realm JSON export is not the identity backup: the entire Keycloak DB is dumped.

Generate 32 cryptographically random key bytes in a protected file, outside Git.
For example, in a private directory with `umask 077`, Python `secrets.token_bytes(32)`.
Do not pass keys/passwords in argv. Rotation requires keeping the old key until
all dependent recovery points expire; loss of a key makes those points unusable.

## Consistency and backup

Reserve an exclusive maintenance window. Exclude direct database/S3 clients and
external integrations; set `external_writers_excluded` true only after verifying
this operational fence. There is no claim of protection against a concurrent
privileged operator bypassing this fence. The command stops all declared writers
with a bounded graceful timeout, verifies stopped state and no remaining clients
on either DB, then captures both DBs and S3. Full table fingerprints are compared
before/after capture. Object key/ETag/size inventory is checked before/after export;
attachment key/SHA256/size/content-type must agree with PostgreSQL.

```sh
/absolute/private/recovery-venv/bin/python infra/backup/recovery.py backup \
  --config /absolute/private/source-recovery.json \
  --key-file /absolute/private/key.bin \
  --archive /absolute/private/backups/UTC-UNIQUE.osbk
```

Only initially running writers restart, including on capture failure. Startup and
available health checks must succeed; a failed resume means a failed command.
A hard process/host crash can leave writers stopped: inspect and restart the
original set under the maintenance procedure; never assume a successful backup.
The controller writes no environment/log/dump contents to stdout/stderr.

The private archive contains native custom-format dumps, TOC, source SHA, UTC,
PostgreSQL versions, complete public-table counts/SHA256, roles/memberships without
password verifiers, object bytes/keys/content-types/user metadata/tags, configuration
allow-list and a SHA256 member manifest. AES-256-GCM authenticates the whole payload
and format header with a random 96-bit nonce, then atomic no-overwrite publication
and filesystem sync. Temporary plaintext uses private directories and is removed;
it is not secure erasure on SSDs. Use an encrypted operator disk and adequate free
space for dump, tar and verified restore staging; object bodies are streamed.

Only current-object unversioned buckets are supported. Versioning enabled **or
suspended**, object-lock and SSE headers are refused; do not disable them just to
pass a test. Provider unsupported-versioning responses are recorded as a coverage
limit. Bucket ACL/policies, lifecycle/replication and provider-specific secrets must
be inventoried/recreated externally; internal disk formats are never copied.

## Restore into an empty isolated target

1. Verify release/images/schema compatibility, private networking, available disk
   and separate secrets. Provision new project/volumes, **same PostgreSQL major**
   and identity release. Create empty databases and original roles with the same
   attributes/memberships but externally recovered passwords; no migrations/demo
   seed or Keycloak startup. PostgreSQL/Redis/S3 alone may start. Recover the
   original OIDC client/hostname/issuer and S3 bucket configuration deliberately.
2. Use a separate protected target config/state directory, new empty buckets and
   all writers stopped. The source and target bucket names must match; provider
   neutrality does not imply automatic bucket remapping.

```sh
/absolute/private/recovery-venv/bin/python infra/backup/recovery.py restore \
  --config /absolute/private/target-recovery.json \
  --key-file /absolute/private/key.bin \
  --archive /absolute/private/backups/UTC-UNIQUE.osbk
```

3. Decryption/authentication, exact members/checksums, DB roles/versions, object
   manifest and target emptiness are checked before mutation. Relations, functions,
   types, non-public schemas and extensions count as nonempty. Ownership and ACL
   restore from the native dumps; restore operator needs appropriate privileges.
   All rows are fingerprinted again and object bytes/metadata/tags re-read.
4. An fsynced `restore-in-progress.json` fences an interrupted/failed target. Never
   clear it and retry in place: preserve it for diagnosis and provision another
   empty target. Successful integrity verification leaves services **stopped**;
   `restore-verified.json` is evidence, not authorization to open ingress.
5. Use a fresh Redis transport; do not restore obsolete queued messages. Start the
   controlled target and worker/scheduler reconciliation, verify Keycloak login,
   application permissions/revocations, scientific results/provenance, audits,
   attachments and new jobs. Do not apply unrecorded migrations. Human acceptance
   and operational authorization are separate from byte/row integrity.

## Off-host copies and retention

A same-host volume does not survive host loss. Provision an approved external
mounted filesystem with private permissions, or use an independently secured pull
account/channel. The tooling accepts an arbitrary explicit mounted destination;
no SSH credentials, mount, network permission or schedule is created automatically.
The destination must support Unix private modes, hard links and fsync; unsupported
filesystems fail rather than weakening these semantics.

```sh
python infra/backup/retention.py transfer --source /private/backups/POINT.osbk \
  --destination /approved/external/POINT.osbk --key-file /private/key.bin
python infra/backup/retention.py prune --destination /approved/external \
  --key-file /private/key.bin --keep APPROVED_COUNT --minimum-age-days APPROVED_DAYS
# Inspect dry-run count, then repeat with --apply after operational approval.
```

Transfer authenticates source/destination, compares SHA256 and syncs before atomic
publication. Retention authenticates **every** `.osbk` point before deleting any,
keeps at least one and refuses links/corrupt points; unrelated files are untouched.
Do not run retention/transfer concurrently with another backup operator. Keep a
known restored copy on a different failure domain before pruning. A mounted
external filesystem's actual durability, access control and availability need
owner approval; a local-directory unit test does not establish off-host recovery.

No RPO/RTO is imposed. Consider daily coordinated full backups for this small pilot
and periodic isolated restores, then approve frequency/retention only after volume,
maintenance downtime and loss tolerance are measured. No WAL/PITR or online backup
is claimed. No scheduled task is installed on any machine by this work.
