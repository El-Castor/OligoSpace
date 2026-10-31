# R1-06 — Pilot upload policy

2026-10-31; implementation of confirmed D2, not a new roadmap.

## Contract

`UPLOADS_ENABLED=false` is the default in every environment. Development/test
may explicitly opt in; production always refuses uploads even with opt-in.
`GET /api/v1/laboratory/upload-policy` requires authentication and reports the
effective policy. The server-rendered upload component reads that policy and
fails closed if unavailable. No public client-side flag controls authorization.

The authenticated multipart endpoint returns 403 `uploads_disabled` before its
explicit file read, parent lookup, object write or Attachment/audit mutation.
Transport multipart parsing may still spool the request; this policy does not
claim to replace reverse-proxy body-size limits. The error reveals no parent ID.
Existing attachment metadata, objects and audit records remain; no migration,
cleanup or publication/download capability is introduced.

## Verification

Four unit regressions were observed failing before implementation, then pass.
Default denial is checked in development/test/production, including no file read
or object/metadata commit. Production opt-in remains ineffective. PostgreSQL tests
retain a real quarantined attachment and compare object contents, Attachment IDs
and audit IDs before/after refused run/validation uploads by admin/viewer.
Explicitly enabled tests retain quarantine/hash/type/size/permission/audit coverage.
Chromium verifies the pilot notice, absence of file input and persistence after
reload while continuing the run/validation lifecycle. Quality and CI evidence is
recorded in the delivery PR and project status.
