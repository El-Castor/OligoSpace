FROM mambaorg/micromamba:2.4.0@sha256:10bd2dd2e7bfae77e529c76a71f4126c222d74e99b908abc6e210da9eda0f6af

USER root
# Apply maintained Debian security fixes; scanner records residual unpatched advisories.
RUN apt-get update \
    && apt-get upgrade --yes \
    && rm -rf /var/lib/apt/lists/*
COPY envs/api.yml /tmp/environment.yml
RUN PIP_NO_CACHE_DIR=1 micromamba install --yes --name base --file /tmp/environment.yml \
    && micromamba clean --all --yes

WORKDIR /app
COPY apps/api/ /app/
RUN PIP_NO_CACHE_DIR=1 micromamba run --name base pip install --no-cache-dir --no-deps . \
    && rm -rf /root/.cache/pip \
    && chown -R ${MAMBA_USER}:${MAMBA_USER} /app

USER ${MAMBA_USER}
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["micromamba", "run", "--name", "base", "uvicorn", "oligospace_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
