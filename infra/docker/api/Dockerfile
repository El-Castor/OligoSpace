# syntax=docker/dockerfile:1.7
FROM ubuntu:24.04@sha256:fe81560990fae86dc4743202b2cb4d3df98d0bcf949173cecef15ce1127ef852 AS runtime-base
# BuildKit verifies HTTPS and the fixed archive hash before the minimal image
# has a CA store. Only public Ubuntu trust anchors bootstrap snapshot HTTPS.
ADD --checksum=sha256:f9fbacd417b515450b831032cc39d18059e9874e67525679a43c16071dabf9a0 \
    https://snapshot.ubuntu.com/ubuntu/20261109T120000Z/pool/main/c/ca-certificates/ca-certificates_20260816ubuntu0.24.04.2_all.deb \
    /tmp/ca-bootstrap.deb
RUN dpkg-deb --extract /tmp/ca-bootstrap.deb /tmp/ca-bootstrap \
    && mkdir -p /etc/ssl/certs \
    && cat /tmp/ca-bootstrap/usr/share/ca-certificates/mozilla/*.crt > /etc/ssl/certs/ca-certificates.crt \
    && rm -rf /tmp/ca-bootstrap /tmp/ca-bootstrap.deb
# Official Noble snapshots retain normal archive signature and validity checks.
RUN printf '%s\n' 'APT::Snapshot "20261109T120000Z";' > /etc/apt/apt.conf.d/50snapshot \
    && apt-get update \
    && apt-get upgrade --yes \
    && apt-get install --yes --no-install-recommends python3.12 ca-certificates libstdc++6 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && test "$(id -u ubuntu)" = 1000 \
    && test "$(id -g ubuntu)" = 1000
ENV PATH=/opt/venv/bin:/opt/primer3/bin:/opt/ncbi-blast/bin:$PATH PYTHONUNBUFFERED=1

FROM runtime-base AS dependencies
RUN apt-get update \
    && apt-get install --yes --no-install-recommends python3.12-venv \
    && rm -rf /var/lib/apt/lists/* \
    && python3.12 -m venv /opt/venv
COPY infra/hardening/locks/api.txt /tmp/runtime.txt
RUN python -m pip install --no-cache-dir --require-hashes -r /tmp/runtime.txt

FROM dependencies AS wheel-builder
COPY infra/hardening/locks/build.txt /tmp/build.txt
RUN python3.12 -m venv /opt/build \
    && /opt/build/bin/python -m pip install --no-cache-dir --require-hashes -r /tmp/build.txt
COPY apps/api /src
RUN /opt/build/bin/python -m pip wheel --no-deps --no-build-isolation --wheel-dir /wheels /src

FROM dependencies AS application
COPY --from=wheel-builder /wheels /wheels
RUN python -m pip install --no-cache-dir --no-deps /wheels/*.whl \
    && rm -rf /wheels /tmp/runtime.txt

FROM application AS tooling
COPY infra/hardening/locks/tooling.txt /tmp/tooling.txt
RUN python -m pip install --no-cache-dir --require-hashes -r /tmp/tooling.txt \
    && rm /tmp/tooling.txt
COPY --chown=1000:1000 apps/api /app
WORKDIR /app
USER 1000:1000
CMD ["python", "-m", "pytest"]

# Remove installer bytes before the environment enters any final runtime layer.
FROM application AS runtime-env
RUN python -m pip uninstall --yes pip setuptools

FROM runtime-base AS runtime
COPY --from=runtime-env /opt/venv /opt/venv
COPY --chown=1000:1000 apps/api/alembic.ini /app/alembic.ini
COPY --chown=1000:1000 apps/api/alembic /app/alembic
WORKDIR /app
USER 1000:1000
EXPOSE 8000
CMD ["uvicorn", "oligospace_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
