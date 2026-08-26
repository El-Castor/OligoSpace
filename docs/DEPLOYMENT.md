# Deployment

## Development

Copy `.env.example` to `.env`, replace every marked development value, then run
`docker compose up --build`. Caddy exposes the web application, API, and OIDC paths
on the configured local HTTP port. Direct host ports for dependent services are
restricted to the development override when needed.

For Python-only work, create `envs/api.yml` or `envs/bioinfo.yml` with Conda and run
the corresponding `make` targets. Node tooling is managed by pnpm/Corepack, not
Conda.

## Production

Use an external secret manager or protected environment file, a real hostname,
institution-approved TLS, pinned images, persistent volumes, and off-host encrypted
backups. Run database migrations as a one-shot deployment job before switching API
traffic. Bootstrap Keycloak administration only on its private network and remove
bootstrap variables after initial configuration.

No institutional domain, identity federation, storage endpoint, or server address
is assumed. Those inputs remain deployment configuration.
