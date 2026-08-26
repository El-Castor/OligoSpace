FROM mambaorg/micromamba:2.4.0 AS primer3-builder

ARG PRIMER3_VERSION=2.6.1

USER root
RUN micromamba install --yes --name base --channel conda-forge \
      c-compiler=1.8.0 cxx-compiler=1.8.0 make=4.4.1 \
    && micromamba clean --all --yes
ADD --checksum=sha256:805cef7ef39607cd40f0f5bb8b32e35e20007153a0a55131dd430ce644c8fb9e \
    https://codeload.github.com/primer3-org/primer3/tar.gz/refs/tags/v2.6.1 \
    /tmp/primer3.tar.gz
RUN set -eu; \
    tar -xzf /tmp/primer3.tar.gz -C /tmp; \
    micromamba run --name base make --directory "/tmp/primer3-${PRIMER3_VERSION}/src" primer3_core oligotm ntthal; \
    install -d /opt/primer3/bin; \
    install -m 0755 "/tmp/primer3-${PRIMER3_VERSION}/src/primer3_core" /opt/primer3/bin/primer3_core; \
    install -m 0755 "/tmp/primer3-${PRIMER3_VERSION}/src/oligotm" /opt/primer3/bin/oligotm; \
    install -m 0755 "/tmp/primer3-${PRIMER3_VERSION}/src/ntthal" /opt/primer3/bin/ntthal

FROM mambaorg/micromamba:2.4.0

ARG TARGETARCH
ARG BLAST_VERSION=2.17.0

USER root
COPY envs/bioinfo.yml /tmp/environment.yml
RUN micromamba install --yes --name base --file /tmp/environment.yml \
    && micromamba clean --all --yes
RUN set -eu; \
    case "${TARGETARCH}" in \
      arm64) archive="ncbi-blast-${BLAST_VERSION}+-aarch64-linux.tar.gz"; checksum="5f9d49b999346e0ddb6637b71af4b22a" ;; \
      amd64) archive="ncbi-blast-${BLAST_VERSION}+-x64-linux.tar.gz"; checksum="bdec166721de3b55f90a3badc83538e8" ;; \
      *) echo "Unsupported BLAST architecture: ${TARGETARCH}" >&2; exit 2 ;; \
    esac; \
    /opt/conda/bin/python -c "import urllib.request; urllib.request.urlretrieve('https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/${BLAST_VERSION}/' + '${archive}', '/tmp/${archive}')"; \
    echo "${checksum}  /tmp/${archive}" | md5sum --check -; \
    tar -xzf "/tmp/${archive}" -C /opt; \
    mv "/opt/ncbi-blast-${BLAST_VERSION}+" /opt/ncbi-blast; \
    rm "/tmp/${archive}"
COPY --from=primer3-builder /opt/primer3 /opt/primer3

WORKDIR /worker
COPY services/bioinfo-worker/ /worker/
RUN micromamba run --name base pip install --no-deps . \
    && chown -R ${MAMBA_USER}:${MAMBA_USER} /worker

USER ${MAMBA_USER}
ENV PYTHONUNBUFFERED=1
ENV PATH="/opt/primer3/bin:/opt/ncbi-blast/bin:${PATH}"
ENV LD_LIBRARY_PATH="/opt/conda/lib:/opt/ncbi-blast/lib"
CMD ["micromamba", "run", "--name", "base", "celery", "--app", "oligospace_bioinfo.celery_app:app", "worker", "--loglevel=INFO"]
