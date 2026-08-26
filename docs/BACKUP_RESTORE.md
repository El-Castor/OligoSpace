# Backup and restore

## Scope and recovery objectives

Back up PostgreSQL consistently, MinIO objects, Keycloak configuration/database,
and deployment configuration excluding plaintext secrets. Choose RPO/RTO with the
institution; the initial recommendation is daily full backups, WAL for point-in-
time recovery, 30 daily and 12 monthly retention points, and quarterly restore
tests.

## Modes

- Mode A (inside INRAE): pgBackRest writes encrypted repositories to controlled
  secondary storage; MinIO versioning/replication targets a separate controlled
  system.
- Mode B (hosted elsewhere): the application produces encrypted, integrity-signed
  backup artifacts. An INRAE host pulls them over a restricted outbound-capable
  account. No inbound route into the institutional network is required.

## Restore test

1. Select a backup and record its checksum, PostgreSQL version, and WAL boundary.
2. Restore into an isolated disposable network and empty volumes.
3. Start PostgreSQL, apply no unrecorded migrations, and run integrity queries.
4. Restore objects and verify a sample against database checksums.
5. Start Keycloak/API/web and execute the smoke journey: authenticate, find an
   oligo, open its assay, and retrieve a test attachment.
6. Record duration, lost-data window, errors, and evidence; destroy test secrets.

Archive creation alone is not success. `infra/backup/restore-test.sh` is currently
a guarded scaffold until repository endpoints and institutional credentials exist.
