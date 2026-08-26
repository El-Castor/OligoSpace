#!/usr/bin/env python3
from __future__ import annotations

import secrets
from pathlib import Path


def token() -> str:
    return secrets.token_urlsafe(36)


target = Path(".env")
if target.exists():
    raise SystemExit(".env already exists; refusing to overwrite it")

development_password = token()
content = f"""# Generated local-only credentials. Never reuse these in production.
ENVIRONMENT=development
AUTH_MODE=development
APP_ORIGIN=http://oligospace.localhost:8080
APP_PORT=8080
POSTGRES_PASSWORD={token()}
NEXTAUTH_SECRET={token()}
KEYCLOAK_ADMIN_USERNAME=admin
KEYCLOAK_ADMIN_PASSWORD={token()}
KEYCLOAK_CLIENT_SECRET={token()}
DEVELOPMENT_USER_PASSWORD={development_password}
MINIO_ROOT_USER=oligospace-local
MINIO_ROOT_PASSWORD={token()}
"""
target.write_text(content, encoding="utf-8")
target.chmod(0o600)
print("Created .env with mode 0600.")
print("Credentials are stored only in .env; inspect that local file when needed.")
