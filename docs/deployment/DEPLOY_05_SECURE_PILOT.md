# DEPLOY-05 — Secure private pilot configuration

Status: implementation under qualification in [PR #23](https://github.com/El-Castor/OligoSpace/pull/23).
Base `36b0bf682a4725a541aa7a71fb7dfd082191bff5`, after DEPLOY-04 PR22 merge.
No real installation, server connection, image publication or supplier adoption.

## Architecture and security contracts

Completes the existing pilot definition rather than introducing a new framework.
Caddy private HTTPS443 -> Web/API/production Keycloak; private application/data
networks isolate PostgreSQL, Redis, S3, worker and scheduler. No public database,
broker, S3, management or Caddy admin port; no build/code bind/default seed/dev auth.
User-configured approved digest references, distinct project volumes and non-root
UIDs, bounded memory/CPU/PIDs, bounded logs, graceful stops and health checks.
Keycloak alone retains a writable root for production startup augmentation; no
scientific permissions are broadened. Runtime egress is removed from API/Web
because their canonical OIDC endpoint resolves to the private proxy.

External canonical host, certificate/chain/key/CA and exact nonsecret proxy/identity
templates are checked. The HTTPS-only topology deliberately has no public HTTP
listener/fallback. Caddy replaces untrusted proxy headers and denies provider admin,
master realm and observability routes. OligoSpace's own authenticated `/admin`
page and server authorization remain intact. Python/Node and the pilot browser
trust the explicit CA; no production trust bypass is introduced.

`doctor.py` is read-only and emits fixed rules/statuses. Unknown availability,
engine disk, real DNS/TLS/access, storage approval, vault/offhost and resources
are never fabricated PASS. Local image presence is distinct from release approval.
AUTH-B6 is not expanded into this lot: no cache/revocation change, and the missing
bounded JWKS cache/rotation remains explicitly BLOCKED before activation. Owner
pilot authorization is also mandatory; activation is always blocked in this lot,
even if input release JSON claims every gate passed. No real activation executor.

## Operations and reuse

[Deployment runbook](../DEPLOYMENT.md) covers external configuration, diagnostic,
controlled synthetic migration, maintenance, backup/empty-target restore and
rollback. `maintenance.py` delegates to DEPLOY-04 Recovery without duplication;
it refuses all non-disposable execution targets. Existing bootstrap roles and
advisory locks are reused, including positive/negative worker permissions.
No scientific architecture or Primer3 parameters were changed. Caddy alone has
NET_BIND_SERVICE because the official binary carries that file capability; all
other capabilities remain dropped and non-root/NNP/read-only remain enforced.

## Qualification matrix

| Area | Current evidence | Status |
|---|---|---|
| Resolved Compose/unsafe configuration refusals | Targeted executable contracts | PASS |
| File protection and temporary certificate chain/name/key | Actual OpenSSL/crypto tests, wrong host/key rejected | PASS |
| Non-destructive preflight/mandatory activation blockers | Targeted tests, no real target execution | PASS |
| Controlled PG role/bootstrap/migration and offline KC import | Actual cached ARM64 component probe, four bounded roles and HEAD verified | PASS (cached scope) |
| Production HTTPS/PKCE/refresh/logout/revocation/MFA/institute isolation | Full16 browser cases prepared | NOT_VERIFIED |
| Scientific worker/Primer3 nine references/BLAST | Actual cached worker measurements and exact BLAST fixture, timeout/exit pass | PASS (direct/cached only) |
| DNS+direct-IP negative ingress/network probe | Six private dependencies,14 endpoints refused; source and restored target | PASS (cached scope) |
| Restart and DEPLOY-04 restore into fresh pilot target | Actual cached ARM64 two-DB/S3 restore and nine-component restart | PASS (cached scope) |
| Native ARM64/AMD64 complete qualification | CI43010939817 failed before boot on upstream downloads | BLOCKED |
| Real supplier/registry/license/provenance/security | Existing DEPLOY-02/03 findings unchanged | BLOCKED |
| AUTH-B6 / owner pilot authorization | Explicit mandatory guard | BLOCKED |
| Real DNS/cert/vault/Cloudflare/Mac mini/offhost/RPO/RTO/human acceptance | Outside synthetic scope | NOT_VERIFIED |

First CI reached passing deployment-contract tests but both native pilot jobs
failed at their first API build, before boot, with registry/network failures.
Other existing native workflows independently report HTTP503 from the fixed
Ubuntu snapshot InRelease endpoints. No assertion/hash/TLS setting is relaxed;
no failed build is claimed as functional qualification. Temporary component-only
probes must stay separate from full browser/scientific/restore acceptance.

## Remaining risks and DEPLOY-06 decision

Ubuntu vendor severity/CVSS disagreements and all DEPLOY-02/03 publication gates
remain blocking. S3 provider/license/logging/transferability (including Garage
access-ID exposure on unsupported tagging), real TLS/DNS, owner-controlled secret
vault, off-host restoration/RPO/RTO, AUTH-B6, real Cloudflare access, memory/disk
margins on the Mac mini and R1-10/R1-11 human acceptance are not closed by tests.
A disposable SeaweedFS fixture is not an adoption or a real MinIO certification.

DEPLOY-06 needs a separate owner authorization after exact-source native/recovery
proof and independent review, approved artifact/supplier decisions and closure
of mandatory security/identity/operational/human gates. No automatic merge or
next-lot execution follows this PR. Independent code review is complete; full
final-source native qualification remains unverified.

## Actual component and recovery evidence (explicitly limited scope)

[Cached component probe](../../infra/deployment/evidence/deploy05/component-probe-cached-arm64.json):
production Keycloak/PostgreSQL bootstrap, four bounded service roles, controlled
migration executed twice (HEAD0004), strict HTTPS/discovery and five headers,
reserved routes404,14 DNS/direct-IP negatives and all nine service log gates PASS.
The temporary host root is private; no real identity/domain/certificate is used.

[Direct worker facts](../../infra/deployment/evidence/deploy05/runtime-science-probe-cached-arm64.json):
nine Primer3 reference values match unchanged1e-6 tolerances, exact synthetic BLAST
match, timeout and exit classifications PASS. These calculations were direct calls;
they were **not persisted asynchronous jobs**, and do not replace scientific7.

[Actual Recovery](../../infra/deployment/evidence/deploy05/science-recovery-probe-cached-arm64.json):
DEPLOY-04 code captures/restores both databases and a sentry S3 object into a fresh
target, verifies fidelity and restarts the nine components. Source/cible network
and logs PASS. Measured Recovery.backup18.957s / restore10.539s exclude transport
setup, outer pause/resume and application readiness: **not RTO/RPO**. Scientific
job/result tables were empty; full scientific persisted-data coverage is not claimed.

All these facts use actual cached local ARM64 Docker IDs, recorded with architecture.
They are not a clean final-SHA image build, AMD64 or browser acceptance. Full CI
still requires16 OIDC and7 scientific cases without skips plus recovery.

## Observed corrections and independent review

- Official Caddy file capability made empty bounding set fail exec255/EPERM.
  Only NET_BIND_SERVICE is admitted for Caddy; cached non-root execution validated.
- Caddy sorted a bare restricted respond after fallback; grouping it in a handle
  restores the intended404 contract. The response had been a Next redirect, not
  an exposed Keycloak console. OligoSpace/admin exact remains authenticated UI.
- Compose create has no --no-deps; corrected helper uses create --pull never --no-build.
- Doctor configuration/CA files could be group/world writable. All022 writes now
  refuse; actualchmod666/664/660 tests reproduced failure then pass after correction.

[Independent review](../../infra/deployment/evidence/deploy05/independent-review.json)
found no other confirmed important code defect.128 deployment contracts and23 auth
runner tests pass locally; full native runtime remains blocked as in the matrix.

## Implementation-commit CI observation

At `ba316cbc61df6ac9f90c3a1c8ad16340efca23e3`, [application CI](https://github.com/El-Castor/OligoSpace/actions/runs/43016760999)
passes backend lint/format/types/tests, frontend lint/types/tests/build, PostgreSQL
integration and migration upgrade/downgrade/upgrade. Compose and worker builds
fail fetching the unchanged signed Ubuntu snapshot InRelease (HTTP502/503).
[Foundation](https://github.com/El-Castor/OligoSpace/actions/runs/43016761247)
passes deployment contracts, then fails the API build at the same upstream.
[Native pilot](https://github.com/El-Castor/OligoSpace/actions/runs/43016760998)
passes operator safety contracts on both architectures, then both jobs fail at
the first API build with `pilot_qualification_command_failed:network,build`,
before startup. The 16 OIDC cases do not execute; scientific/recovery steps are
skipped. Full native browser/scientific results remain NOT_VERIFIED.
These failures are not scientific assertions,
and no source pin, checksum or TLS requirement was weakened. Later reporting-only
changes do not make these unexecuted runtime checks pass.

## Final targeted availability check — 2026-11-11

The remote branch still matched `730b10691cc44676ab57acff6e69426c8cd47429`.
Its [foundation run](https://github.com/El-Castor/OligoSpace/actions/runs/43058413437),
job130654028418, fails even earlier: the runner resolver127.0.0.53 times out
resolving archive.ubuntu.com for the unchanged checksum-pinned CA package.
Both [native pilot jobs](https://github.com/El-Castor/OligoSpace/actions/runs/43058413205)
(130654004606 AMD64,130654005084 ARM64) fail at their first API build, before boot.

[One bounded independent probe](../../infra/deployment/evidence/deploy05/upstream-availability.json)
at16:50UTC preserves normal HTTPS verification: all three frozen snapshot
InRelease URLs time out connecting443; the exact official CA package and current
official ports archive return200. Thus the earlier runner DNS failure is distinct
from the still-unreachable snapshot endpoint. No available equivalent immutable
source was established; the moving archive is not a substitute for the dated
signed snapshot. No dependency/source/signature/checksum/TLS/gate was changed.

Reproduce each recorded URL once with
`curl --silent --show-error --location --max-time 12 --connect-timeout 8 --output /dev/null --write-out '%{http_code}' URL`.
Exit28/HTTP000 records a connection timeout, not an HTTP502/503 response.
No new full qualification campaign or redundant green tests were launched.
**Decision: BLOCKED** until the immutable source is reachable and the required
native OIDC/scientific/recovery qualification can execute. Stop here; no merge,
deployment or DEPLOY-06.
Independent review of this final documentation/evidence delta found no important
anomaly; it confirmed the separate timeout/HTTP/DNS observations and BLOCKED status.
