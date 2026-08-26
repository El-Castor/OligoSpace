FROM mcr.microsoft.com/playwright:v1.62.1-noble

WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY --chown=pwuser:pwuser apps/web/ ./

USER pwuser
CMD ["npm", "run", "test:e2e"]
