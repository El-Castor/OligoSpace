# DEPLOY-03 — Container hardening and security remediation

**Goal:** Deliver one reviewed PR containing an evidence-based API/worker runtime
choice, reproducible dependency controls and native dual-architecture qualification.
**Source specification:** owner attachment, DEPLOY-03 phases A–F, 2026-11-09.
**Base:** `9ebbf2cd993395af2b154efb0b4cf5a76b4dd079`.
**Branch:** `codex/deploy-03-container-hardening`.

## Constraints and design

No publication, merge, real deployment/migration, Mac mini, Cloudflare, S3 provider
change, scanner suppression, scientific parameter/reference or business-rule change.
Preserve personal `assests/` and pre-existing generated `next-env.d.ts` changes.
Qualification uses tracked-source archives, temporary local resources and native
ARM64/AMD64 CI runners. Emulated execution is labelled separately. Preserve distro,
Conda and pip metadata, licenses and complete severity counts. No sid/stable mixing.

The owner's specified three-way experiment determines the choice; no base switch
is approved by a count alone. A: current micromamba with production dependencies
only. B: same-prefix environment/scientific artifacts transferred into a minimal
maintained runtime, with explicit shared-library closure and activation checks.
C: another maintained glibc distribution/runtime with Python 3.12 and locked wheels.
Python patch updates are security changes to document and qualify, never grounds
to change golden scientific results. Keep `kombu==5.6.2`.

## Execution and review gates

- [x] Read request, current status, Docker/env/dependency/scanner code and relevant
  memory. Verify base and create the sole branch without including personal files.
- [x] A — Freeze historical inventory (nine distinct Debian CVEs versus 176 binary
  occurrences across four artifacts), current source/digests/packages/SBOM and fresh
  baseline OCI scans before modifying production images. Mark absent CVSS/layer/
  exploitability facts as unknown. Record scanner and vulnerability DB identity.
- Native comparison at `9020258` completed for all four role/architecture pairs:
  all three initial candidates retain unresolved Tk closure; Bookworm adds two
  CRITICAL findings. Reports and common-DB summary retained. A fourth Ubuntu LTS
  variant was selected after native qualification; final production proof follows at7b9dca4.
- [x] B — Build/scan the three candidates, retaining all severities, package metadata,
  exact source/platform identity and final OCI sizes. Execute native import/ELF,
  Primer3 nine-fact and BLAST fixtures. Reject unmaintained or unobservable options.
- [x] C/D — Select demonstrated candidate; separate tooling from production runtime,
  lock dependency closure without drifting Kombu, verify downloads, and document ADR
  if the container strategy changes. Preserve existing command interfaces where
  needed by qualification tooling, with explicit exceptions rather than silent skips.
- [x] C/E — Run isolated non-root/read-only/capability/no-new-privileges/resource/
  network/secret/stop probes; execute PostgreSQL/migrations, API/web, real Keycloak,
  Chromium, Redis/Celery/idempotency and MVP-02 on candidates. Qualify S3 adapter
  without adopting a supplier. Native CI on both architectures; no emulation claim.
- [x] F — Independent review; correct demonstrated issues and rerun affected checks.
  Deliver `docs/deployment/DEPLOY_03_CONTAINER_HARDENING.md`, inventory before/after,
  strategy matrix, residual risks and DEPLOY-04 recommendations. Update project
  tracking and Basic Memory. One PR, final SHA/CI results; stop unmerged.

## Validation focus

Missing scanner inventory must fail coverage rather than look like zero CVEs.
All scores retain vendor/source and unknown values; Debian urgency is not CVSS.
CA trust, dynamically loaded libraries, activation hooks and writable temporary
paths must be executed, not inferred from a successful image build. Runtime probes
must not access development data or the Docker socket. Scientific facts, roles,
provenance and active-request deduplication remain unchanged. Historical DEPLOY-02
scan failures and unresolved storage/provenance/license gates remain visible.

## Outcome — 2026-11-10

Delivered for review in PR21. Selected maintained Ubuntu runtime after all four
strategies were executed natively. Final code7b9dca4 passes all mandatory make,
PostgreSQL206, Chromium29, OIDC16 and scientific7 cases per native architecture,
plus runtime/cleanstop and8S3contracts. Primer3 nine references remain unchanged;
Kombu5.6.2 retained. Targeted JWT/multipart/Biopython security fixes qualified;
BiopythonHIGH missed by scanner corrected from authoritative upstream advisory.
Final common-DB scans complete with0detectedCRITICAL/HIGH,22MEDIUM/4LOW and0secrets.
Higher upstream CVSS scores, unresolved vendor statuses and all release gates
remain open. Final report records manifests, size reductions, complete finding
receipts, independent review and limitations. No merge/publication/deployment or
DEPLOY-04. Personal files preserved; next action is owner PR review.
