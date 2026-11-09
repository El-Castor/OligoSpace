# Disposable runtime qualification

`isolated_runtime.py` accepts existing local API, worker, PostgreSQL and Redis
images. It never pulls images, connects to development services, publishes host
ports or mounts the Docker socket. PostgreSQL must use the Alpine image's UID 70;
Redis runs as UID 999, and applications as UID 1000. The image defaults launch
the applications, preserving their entrypoints and activation behavior.

```sh
python3.12 infra/hardening/isolated_runtime.py \
  --context default \
  --api-image oligospace-qualification/api-strategy-c:SOURCE_SHA \
  --worker-image oligospace-qualification/worker-strategy-c:SOURCE_SHA \
  --postgres-image postgres:17.11-alpine \
  --redis-image redis:7.4-alpine \
  --output /tmp/qualification/runtime.json
```

Use reviewed digest references for supplier images when available. The report
records the locally resolved image IDs and architectures. For Conda candidates,
pass `--api-python /opt/conda/bin/python` and
`--worker-python /opt/conda/bin/python`; these paths affect probes only, never
the application startup command.

All services use one unique internal network, non-root users, a read-only rootfs,
all capabilities dropped, no-new-privileges, CPU/PID/memory limits and bounded
tmpfs. PostgreSQL and Redis data exist only in tmpfs. Docker injects generated
application credentials from a private mode-0600 env file, also mounted read-only;
applications do not need to read that reference file. Redis receives its generated
password in a read-only config file accessible inside a private mode-0700
temporary directory. No generated values or raw logs enter evidence.

Checks cover inspected runtime controls, API live/ready (including a real
PostgreSQL query), Celery broker/control ping through authenticated Redis,
generated credentials absent from both log streams, bounded graceful stop and
cleanup of the unique Compose project. Containers are removed without volume
pruning. The controller's subprocesses run on the host; the socket is never
mounted inside a container.

The fixture deliberately uses test/development authentication and an empty test
database. Migrations, RLS/OIDC, scientific job execution, idempotency and real
Keycloak integration remain explicitly `not_verified`. This tool does not replace
`infra/auth-qualification/run.py` or provide scientific equivalence evidence.
