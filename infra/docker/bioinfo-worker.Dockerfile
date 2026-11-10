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
RUN printf '%s\n' \
    'Types: deb' \
    'URIs: https://snapshot.ubuntu.com/ubuntu/20261109T120000Z' \
    'Suites: noble noble-updates noble-security' \
    'Components: main universe' \
    'Signed-By: /usr/share/keyrings/ubuntu-archive-keyring.gpg' \
    > /etc/apt/sources.list.d/ubuntu.sources \
    && apt-get update --error-on=any \
    && apt-get upgrade --yes \
    && apt-get install --yes --no-install-recommends python3.12 ca-certificates libstdc++6 libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && test "$(id -u ubuntu)" = 1000 \
    && test "$(id -g ubuntu)" = 1000
ENV PATH=/opt/venv/bin:/opt/primer3/bin:/opt/ncbi-blast/bin:$PATH PYTHONUNBUFFERED=1

ENV LD_LIBRARY_PATH=/opt/ncbi-blast/lib

FROM runtime-base AS primer3-builder
RUN apt-get update --error-on=any \
    && apt-get install --yes --no-install-recommends gcc g++ make \
    && rm -rf /var/lib/apt/lists/*
ADD --checksum=sha256:805cef7ef39607cd40f0f5bb8b32e35e20007153a0a55131dd430ce644c8fb9e \
    https://codeload.github.com/primer3-org/primer3/tar.gz/refs/tags/v2.6.1 \
    /tmp/primer3.tar.gz
RUN tar -xzf /tmp/primer3.tar.gz -C /tmp \
    && make --directory /tmp/primer3-2.6.1/src primer3_core oligotm ntthal \
    && install -d /opt/primer3/bin \
    && install -m 0755 /tmp/primer3-2.6.1/src/primer3_core /tmp/primer3-2.6.1/src/oligotm /tmp/primer3-2.6.1/src/ntthal /opt/primer3/bin/

FROM runtime-base AS blast-builder
ARG TARGETARCH
# SHA256 pins are locally computed, not upstream-authenticated attestations.
# Keep NCBI's MD5 check too, and retain the full distribution and legal files.
RUN TARGETARCH="${TARGETARCH}" python3.12 - <<'PYTHON'
import hashlib
import os
from pathlib import Path
import tarfile
import time
import urllib.request

pins = {
    "arm64": ("aarch64", "5f9d49b999346e0ddb6637b71af4b22a", "cb9ac252a1ac8767d90b0bf0a38486f3cb94f71ef9b6b8d194ded19b30250daf"),
    "amd64": ("x64", "bdec166721de3b55f90a3badc83538e8", "3888112d8207831aa47371d93583c601f058f88b5db22dc782438b039a3a411b"),
}
architecture = os.environ["TARGETARCH"]
if architecture not in pins:
    raise SystemExit("unsupported_blast_architecture")
platform, expected_md5, expected_sha256 = pins[architecture]
url = f"https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.17.0/ncbi-blast-2.17.0+-{platform}-linux.tar.gz"
archive = Path("/tmp/blast.tar.gz")
sha256 = hashlib.sha256()
md5 = hashlib.md5()
total = 0
deadline = time.monotonic() + 600
with urllib.request.urlopen(url, timeout=60) as response, archive.open("wb") as destination:
    while chunk := response.read(1024 * 1024):
        total += len(chunk)
        if total > 512 * 1024 * 1024 or time.monotonic() > deadline:
            raise SystemExit("blast_download_limit_exceeded")
        destination.write(chunk)
        sha256.update(chunk)
        md5.update(chunk)
if sha256.hexdigest() != expected_sha256 or md5.hexdigest() != expected_md5:
    raise SystemExit("blast_archive_checksum_mismatch")
with tarfile.open(archive) as source:
    source.extractall("/opt", filter="data")
Path("/opt/ncbi-blast-2.17.0+").rename("/opt/ncbi-blast")
archive.unlink()
PYTHON

FROM runtime-base AS dependencies
RUN apt-get update --error-on=any \
    && apt-get install --yes --no-install-recommends python3.12-venv \
    && rm -rf /var/lib/apt/lists/* \
    && python3.12 -m venv /opt/venv
COPY infra/hardening/locks/worker.txt /tmp/runtime.txt
RUN python -m pip install --no-cache-dir --require-hashes -r /tmp/runtime.txt

FROM dependencies AS wheel-builder
COPY infra/hardening/locks/build.txt /tmp/build.txt
RUN python3.12 -m venv /opt/build \
    && /opt/build/bin/python -m pip install --no-cache-dir --require-hashes -r /tmp/build.txt
COPY services/bioinfo-worker /src
RUN /opt/build/bin/python -m pip wheel --no-deps --no-build-isolation --wheel-dir /wheels /src

FROM dependencies AS application
COPY --from=wheel-builder /wheels /wheels
RUN python -m pip install --no-cache-dir --no-deps /wheels/*.whl \
    && rm -rf /wheels /tmp/runtime.txt
COPY --from=primer3-builder /opt/primer3 /opt/primer3
COPY --from=blast-builder /opt/ncbi-blast /opt/ncbi-blast

FROM application AS tooling
COPY infra/hardening/locks/tooling.txt /tmp/tooling.txt
RUN python -m pip install --no-cache-dir --require-hashes -r /tmp/tooling.txt \
    && rm /tmp/tooling.txt
COPY --chown=1000:1000 services/bioinfo-worker /worker
WORKDIR /worker
USER 1000:1000
CMD ["python", "-m", "pytest"]

# Remove installer bytes before the environment enters any final runtime layer.
FROM application AS runtime-env
RUN python -m pip uninstall --yes pip setuptools

FROM runtime-base AS runtime
COPY --from=runtime-env /opt/venv /opt/venv
COPY --from=primer3-builder /opt/primer3 /opt/primer3
COPY --from=blast-builder /opt/ncbi-blast /opt/ncbi-blast
WORKDIR /worker
USER 1000:1000
CMD ["celery", "--app", "oligospace_bioinfo.celery_app:app", "worker", "--loglevel=INFO"]
