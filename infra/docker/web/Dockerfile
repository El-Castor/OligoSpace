FROM node:22.23.0-alpine3.23 AS dependencies
WORKDIR /app
COPY apps/web/package.json apps/web/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci

FROM dependencies AS tooling
WORKDIR /app
ENV NEXT_TELEMETRY_DISABLED=1
COPY apps/web/ ./

FROM tooling AS builder
RUN npm run build

FROM node:22.23.0-alpine3.23 AS runtime
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN addgroup --system --gid 1001 nodejs \
    && adduser --system --uid 1001 nextjs
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
