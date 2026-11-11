# Deployment

## Development

Copy `.env.example` to `.env`, replace every marked development value, then run
`docker compose up --build`. Caddy exposes the web application, API, and OIDC paths
on the configured local HTTP port. Direct host ports for dependent services are
restricted to the development override when needed.

For Python-only work, create `envs/api.yml` or `envs/bioinfo.yml` with Conda and run
the corresponding `make` targets. Node tooling is managed by pnpm/Corepack, not
Conda.

## Private pilot — prepared configuration, activation blocked

The independent definition is `infra/deployment/compose.pilot.json`; canonical
project `oligospace-pilot`, private ingress443 only, separate project-scoped
networks/volumes and approved immutable image references supplied externally.
There is no `build`, source mount, seed or development identity in this definition.
Do not run raw Compose as a production installer: this lot does not provide an
approved real activation path. [DEPLOY-05 report](deployment/DEPLOY_05_SECURE_PILOT.md)
records the qualification scope and outstanding gates.

### Prepare protected configuration

Copy `infra/deployment/configuration.env.example`, `Caddyfile.template` and
`keycloak.conf.example` outside Git into an operator-controlled directory.
Keep the env file0600 and never print resolved configuration or enable shell
tracing. Supply institution-approved images by digest, canonical host/origin/realm,
certificate chain/private key and trusted CA bundle; no values or production
certificates are generated automatically. File ownership/groups must allow the
actual non-root container UID to read its designated secret, without broadening
access to other users. Test fixtures are temporary and never production credentials.

`PILOT_HOST` has no scheme/path/port; `APP_ORIGIN=https://PILOT_HOST` and
`OIDC_ISSUER=APP_ORIGIN/realms/OIDC_REALM`. The shared canonical hostname resolves
to Caddy on the application network; API/Python and Web/Node explicitly trust the
supplied CA. Keycloak uses production `start`, PostgreSQL `os_identity`, strict
hostname and forwarded headers trusted only from the actual application subnet.
Set `PROXY_TRUSTED_CIDRS` to that approved subnet, never a global/broad range.

HTTPS-only topology: no port80 listener or implicit HTTP fallback. Clients use the
canonical HTTPS URL; HTTP requests are refused rather than redirected through a
public listener. Caddy's admin API, Keycloak admin subtree/master realm, metrics
and provider health endpoints are not published. OligoSpace `/admin` remains its
normal authenticated application page with server-enforced API permissions.
Client-supplied Forwarded/X-Forwarded headers are replaced at the proxy boundary.

### Diagnose without activation

Install Python3.12 operator dependencies from existing DEPLOY-04 hashes in an
isolated venv, then run the read-only controller:

```sh
python3.12 -m venv /absolute/private/operator-venv
/absolute/private/operator-venv/bin/pip install --require-hashes -r infra/backup/requirements.txt
/absolute/private/operator-venv/bin/python infra/deployment/doctor.py \
  --context LOCAL_UNIX_CONTEXT --project oligospace-pilot \
  --env-file /absolute/private/pilot.env \
  --release-evidence /absolute/nonsecret/release-evidence.json \
  --min-memory-gib 8 --min-disk-gib 12
```

It does not pull/start/migrate/create a target or probe a real DNS/server. It checks
actual Compose resolution, protected files, certificate chain/name/expiry/key,
local engine/image architecture and available resources. Image availability and
approval remain distinct; fixture image IDs are never approved release references.
Disk observations from the host are not proof of Docker Desktop's VM free space;
unavailable engine storage observations stay NOT_VERIFIED. Thresholds are
configurable proposals, not a capacity certification of a16-GB Mac mini.

Outputs are PASS/FAIL/BLOCKED/NOT_VERIFIED and fixed rule IDs, never config/secret
values. Return code remains nonzero because activation is BLOCKED: mandatory
AUTH-B6 and owner authorization plus all unresolved release gates cannot be set
to PASS by an input JSON. A structurally valid file is not a deployment approval.

### Maintenance, schema and recovery

Reuse [DEPLOY-04](BACKUP_RESTORE.md), with separate protected backup config/key,
approved off-host destination and independently recoverable vault. Do not duplicate
the backup logic or reuse development volumes. The optional disposable maintenance
wrapper calls the same Recovery implementation and never migrates:

```sh
python infra/deployment/maintenance.py pre-migration --recovery-config /absolute/private/disposable-recovery.json
python infra/deployment/maintenance.py backup --recovery-config /absolute/private/disposable-recovery.json \
  --key-file /absolute/private/key.bin --archive /absolute/private/point.osbk
python infra/deployment/maintenance.py restore --recovery-config /absolute/private/empty-target-recovery.json \
  --key-file /absolute/private/key.bin --archive /absolute/private/point.osbk
```

This executor accepts only `oligospace-pilot-test-*` disposable projects and refuses
a real pilot. Real migration/maintenance execution remains a separately authorized
DEPLOY-06 operation. The existing bootstrap controller serializes initialization
and migration with advisory locks, refuses unknown/nonempty unversioned schema,
verifies head and bounded `os_app`/`os_worker`/`os_identity` roles. No seed, downgrade,
role-password rotation or deletion is automatic. Worker/scheduler share a dedicated
role with job/attempt/result SELECT/INSERT/UPDATE and audit INSERT; no registry
mutation, scientific deletion, schema creation or administrative role.

Before any future update: keep ingress closed, stabilize writers, verify current
images/schema/health, take and verify a coordinated encrypted backup, preserve the
previous release manifest and require explicit compatibility/rollback approval.
After failure stay closed and preserve volumes. Return to previous image digests
only when schema-compatible; otherwise restore the complete coherent point into
an approved empty target and quantify lost writes. Never auto-downgrade or replay
old Redis transport. First installation has no previous release to assume: retain
the failed state and diagnose without deleting data.

### Qualification and conditions for DEPLOY-06

`python infra/deployment/qualify_pilot.py [--scientific]` executes the generated
isolated fixture only; it never reads a real pilot env file. It uses the pilot
template with recorded local-test deviations, temporary TLS/identities, a previously
qualified S3 candidate and immutable local image IDs. Those are not supplier or
publication approvals. Native CI must prove all required cases, without skips or
weakened assertions. Strict browser trust uses only the run's temporary CA.

DEPLOY-06 requires a new explicit owner authorization, successful exact-source
native qualification/review, approved registry/digests and supplier, closure of
mandatory security findings/AUTH-B6, real DNS/TLS/Cloudflare access and vault
procedures, approved off-host backup/restore and RPO/RTO, hardware capacity and
incident recovery, plus R1-10/R1-11 human scientific acceptance. This lot does not
qualify any actual Mac mini, domain, Cloudflare/WARP policy or storage server.
