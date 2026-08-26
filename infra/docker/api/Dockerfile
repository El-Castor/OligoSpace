FROM mambaorg/micromamba:2.4.0

USER root
COPY envs/api.yml /tmp/environment.yml
RUN micromamba install --yes --name base --file /tmp/environment.yml \
    && micromamba clean --all --yes

WORKDIR /app
COPY apps/api/ /app/
RUN micromamba run --name base pip install --no-deps . \
    && chown -R ${MAMBA_USER}:${MAMBA_USER} /app

USER ${MAMBA_USER}
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
CMD ["micromamba", "run", "--name", "base", "uvicorn", "oligospace_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
