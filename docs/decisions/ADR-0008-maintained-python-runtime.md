# ADR-0008: Maintained Ubuntu Python runtime and separate tooling

- Status: implemented and technically qualified for code review; no operational authorization
- Date: 2026-11-10
- Supersedes: ADR-0005 only for API/worker container construction

## Context

Native AMD64/ARM64 comparison retained all scanner metadata and scientific
references. Pruning micromamba did not reduce HIGH findings; transferring Conda
added HIGH occurrences; official Python Bookworm introduced two CRITICAL findings.
All three retained unresolved optional Tk libraries. The fourth Ubuntu 24.04
variant passed native import/library, read-only/non-root, Primer3 and BLAST probes
for both roles on both architectures, with no detected CRITICAL/HIGH findings.
Vendor advisory uncertainty and MEDIUM/LOW findings remain open.

## Decision

Use digest-pinned Ubuntu 24.04, distro-maintained Python 3.12 and a dated signed
apt snapshot. Install exact hashed runtime wheels; retain package metadata and
separate development tools from the default final runtime. Strip pip before the
environment is copied into runtime layers. Keep an explicit tooling target.
Use direct venv commands and preserve exact migration/security contracts.
Historical micromamba experiments and local Conda files remain identified as such.

Primer3 source, parameters and references remain unchanged. BLAST 2.17.0 is
downloaded independently and checked against upstream MD5 plus captured SHA256;
the latter binds observed bytes and is not an upstream signature.

## Consequences and revisit triggers

Qualify production artifacts, all OIDC/scientific paths and mandatory checks on
both native architectures before technical acceptance. Targeted JWT/multipart
security updates require that same authentication regression coverage. Snapshot
and base updates must be reviewed and scanned; snapshot retention is bounded.
Python patch security is supplied through Ubuntu backports, independently of the
legacy Conda Python patch. Reconsider on scientific incompatibility, unsupported
packages, new fixes or material scanner/advisory gaps. This decision grants no
publication, deployment, S3 adoption or release waiver.
