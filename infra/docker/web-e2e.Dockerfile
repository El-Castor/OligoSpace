FROM mcr.microsoft.com/playwright:v1.62.1-noble

RUN apt-get update && apt-get install -y --no-install-recommends libnss3-tools && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci
COPY --chown=pwuser:pwuser apps/web/ ./

USER pwuser
CMD ["npm", "run", "test:e2e"]
