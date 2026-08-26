# Infrastructure scope

- No real secrets, default production passwords, or public database/cache/admin
  ports. Validate required production variables at startup.
- Pin container image versions and run application containers as non-root.
- Public traffic terminates at the reverse proxy over HTTPS; internal dependencies
  use isolated networks.
- Backup changes require a restore-path review and an updated restore test.
- Preserve separate development conveniences and production-safe defaults.
- Run `docker compose config` and relevant image builds after changes.
