# DEPLOY-04 — coordinated backup and verified recovery

User supplied execution specification; autonomous inline execution and independent
review, one branch/PR, no real target or release. Base: origin/main ff3f629,
DEPLOY-03 merged. Personal working tree preserved in separate worktree.

## Targeted findings and design

Existing pg_dump shell exports only one unencrypted DB; restore scaffold drops a
named DB; DEPLOY-02 S3 contracts are synthetic and lack global coordination.
Reuse native PostgreSQL tools, existing OIDC/scientific fixtures and MinIO SDK.
Use logical backup for pilot size; WAL/PITR and uncoordinated online snapshots
are not selected because they do not solve cross-service consistency alone.

Stop and verify all configured writers (API, worker/scheduler, identity/web/ingress),
assert complete stack coverage, capture both databases and S3 while stopped,
then resume only previously running services even on failure. Operator must
exclude external/direct writers; enforce database session exclusion and stable
objects. Redis is disposable transport, not restored. Configuration allow-list
contains non-secret files only; secret *names* only, recovery keys kept separately.
Archive contains UTC/source/schema/versions/content SHA256 and object metadata;
stream AES-256-GCM encryption, private staging, atomic completion. Verify decrypt,
all members/checksums and manifests before target mutation. Require stopped
writers, empty databases and empty storage; fail closed and leave stopped after
any interrupted restore. No automatic override for nonempty targets.

## Tasks and evidence

- [x] Authenticated archive, manifest/path safety and negative tests.
- [x] Provider-independent S3 snapshot and full fidelity verification.
- [x] Coordinated local Compose PG/Keycloak backup, empty-target restore,
      state journal, protected inputs, external destination and retention.
- [x] Native disposable real restoration and OIDC/scientific/integrity tests,
      corruption/missing/wrong-key/interruption/nonempty/secret refusals.
- [x] Relevant targeted tests then mandatory make/CI; independent restore review.
- [x] Report, runbook, STATUS/BACKLOG/CHANGELOG; one PR, no merge/publication.

## Review focus

Never resume a partially restored target; no archive traversal/symlink, omitted
member, unauthenticated plaintext or secret log; never infer consistency from
three independent timestamps. Versioned/object-lock buckets require explicit
support or refusal, not silent loss. Preserve UUIDs/provenance and OIDC subject.
RPO/RTO measured on synthetic corpus, owner approves operational objectives.

## Outcome

Qualified code953f5fb: native recovery42866007006 and application42866006639 PASS
on both architectures;30 backup/107 deployment/26 hardening/23 auth tests PASS.
Two full dumps, S3/attachment fidelity, fresh OIDC/permissions/new scientific job
and11 negatives per platform proven. Independent review findings resolved.
Report docs/deployment/DEPLOY_04_BACKUP_RECOVERY.md; single PR22 delivered for review.
Garage logging remains an open supplier finding; positive SeaweedFS fixture is
not adoption. Release and off-host/vault/RPO/RTO/human gates remain open.
No publication, deployment, real data/volume operation, merge or next lot.
