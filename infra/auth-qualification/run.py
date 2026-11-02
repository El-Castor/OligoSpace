"""Disposable, synthetic-only HTTPS/Keycloak qualification. Never reads .env."""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import uuid
import shutil

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = "https://auth-qualification.test"


def run(command: list[str], *, data: str | None = None) -> None:
    # Captured output may contain authorization URLs or temporary credentials.
    result = subprocess.run(
        command, input=data, text=True, capture_output=True, check=False
    )
    if result.returncode:
        raise RuntimeError(f"Qualification phase failed: {command[0]} {command[1]}")


def main() -> None:
    os.umask(0o077)
    evidence = ROOT / "infra/auth-qualification/evidence"
    evidence.mkdir(exist_ok=True)
    for name in ("synthetic-dashboard.png", "synthetic-administration.png"):
        (evidence / name).unlink(missing_ok=True)
    summary: dict[str, object] = {"qualification": "not_completed", "tests": []}
    (evidence / "summary.json").write_text(json.dumps(summary, indent=2))
    with tempfile.TemporaryDirectory(prefix="oligospace-oidc-") as temporary:
        work = Path(temporary)
        # Bind mounts are consumed by non-root application users; only this disposable
        # directory is traversable. Private key never enters an image or artifact.
        work.chmod(0o755)
        for name in ("certs", "realm"):
            (work / name).mkdir(mode=0o755)
        (work / "evidence").mkdir(mode=0o777)
        (work / "evidence").chmod(0o777)
        password, client_secret, auth_secret, db_password, admin_password = (
            secrets.token_urlsafe(36) for _ in range(5)
        )
        identities = {
            role: str(uuid.uuid4())
            for role in ("admin", "member", "viewer", "pending", "disabled", "mfa")
        }
        realm = json.loads((ROOT / "infra/keycloak/realm-oligospace.json").read_text())
        realm.update(
            realm="qualification",
            displayName="Synthetic qualification",
            sslRequired="external",
            accessTokenLifespan=90,
            ssoSessionIdleTimeout=600,
            ssoSessionMaxLifespan=900,
            rememberMe=False,
            resetPasswordAllowed=False,
        )
        client = realm["clients"][0]
        client.update(
            secret=client_secret,
            redirectUris=[f"{ORIGIN}/api/auth/callback/keycloak"],
            webOrigins=[ORIGIN],
        )
        client["attributes"] = {
            "pkce.code.challenge.method": "S256",
            "post.logout.redirect.uris": f"{ORIGIN}/login",
        }
        realm["users"] = [
            {
                "id": subject,
                "username": f"synthetic-{role}",
                "email": f"{role}@qualification.invalid",
                "firstName": "Synthetic",
                "lastName": role.title(),
                "enabled": True,
                "emailVerified": True,
                "credentials": [
                    {"type": "password", "value": password, "temporary": False}
                ],
                "realmRoles": [
                    role if role in ("admin", "member", "viewer") else "member"
                ],
                "requiredActions": ["CONFIGURE_TOTP"] if role == "mfa" else [],
            }
            for role, subject in identities.items()
        ]
        realm_path = work / "realm/qualification.json"
        realm_path.write_text(json.dumps(realm))
        realm_path.chmod(0o644)
        run(
            [
                "openssl",
                "req",
                "-x509",
                "-newkey",
                "rsa:2048",
                "-nodes",
                "-days",
                "1",
                "-subj",
                "/CN=auth-qualification.test",
                "-addext",
                "subjectAltName=DNS:auth-qualification.test",
                "-addext",
                "basicConstraints=critical,CA:TRUE",
                "-keyout",
                str(work / "certs/key.pem"),
                "-out",
                str(work / "certs/ca.pem"),
            ]
        )
        (work / "certs/ca.pem").chmod(0o644)
        (work / "Caddyfile").write_text("""{
  admin off
  auto_https off
}
https://auth-qualification.test {
  tls /certs/ca.pem /certs/key.pem
  handle /realms/* {
    reverse_proxy keycloak:8080
  }
  handle /resources/* {
    reverse_proxy keycloak:8080
  }
  handle /api/auth/* {
    reverse_proxy web:3000
  }
  handle /api/* {
    reverse_proxy api:8000
  }
  handle {
    reverse_proxy web:3000
  }
}
""")
        (work / "Caddyfile").chmod(0o644)
        db_url = f"postgresql+asyncpg://qualification:{db_password}@postgres:5432/qualification"
        ca_mount = f"{work / 'certs/ca.pem'}:/certs/ca.pem:ro"
        api_env = {
            "ENVIRONMENT": "production",
            "AUTH_MODE": "oidc",
            "UPLOADS_ENABLED": "false",
            "DATABASE_URL": db_url,
            "OIDC_ISSUER": f"{ORIGIN}/realms/qualification",
            "OIDC_AUDIENCE": "oligospace-api",
            "OIDC_CLIENT_ID": "oligospace-web",
            "OIDC_CLIENT_SECRET": client_secret,
            "SSL_CERT_FILE": "/certs/ca.pem",
            "REQUESTS_CA_BUNDLE": "/certs/ca.pem",
            "OBJECT_STORAGE_ACCESS_KEY": secrets.token_urlsafe(24),
            "OBJECT_STORAGE_SECRET_KEY": secrets.token_urlsafe(32),
            "OBJECT_STORAGE_ENDPOINT": "disabled.invalid:9000",
        }
        compose = {
            "networks": {"default": {"internal": True}},
            "services": {
                "postgres": {
                    "image": "postgres:17.11-alpine",
                    "environment": {
                        "POSTGRES_USER": "qualification",
                        "POSTGRES_PASSWORD": db_password,
                        "POSTGRES_DB": "qualification",
                    },
                    "tmpfs": ["/var/lib/postgresql/data"],
                    "healthcheck": {
                        "test": ["CMD-SHELL", "pg_isready -U qualification"],
                        "interval": "2s",
                        "retries": 60,
                    },
                },
                "keycloak": {
                    "image": "quay.io/keycloak/keycloak:26.7.2",
                    "command": ["start-dev", "--import-realm"],
                    "environment": {
                        "KC_HOSTNAME": ORIGIN,
                        "KC_HTTP_ENABLED": "true",
                        "KC_PROXY_HEADERS": "xforwarded",
                        "KC_BOOTSTRAP_ADMIN_USERNAME": "synthetic-bootstrap",
                        "KC_BOOTSTRAP_ADMIN_PASSWORD": admin_password,
                    },
                    "tmpfs": ["/opt/keycloak/data:uid=1000,gid=0"],
                    "volumes": [
                        f"{realm_path}:/opt/keycloak/data/import/qualification.json:ro"
                    ],
                },
                "api": {
                    "build": {
                        "context": str(ROOT),
                        "dockerfile": "infra/docker/api/Dockerfile",
                    },
                    "environment": api_env,
                    "volumes": [ca_mount],
                },
                "web": {
                    "build": {
                        "context": str(ROOT),
                        "dockerfile": "infra/docker/web/Dockerfile",
                    },
                    "environment": {
                        "AUTH_MODE": "oidc",
                        "NEXTAUTH_URL": ORIGIN,
                        "NEXTAUTH_SECRET": auth_secret,
                        "API_INTERNAL_URL": "http://api:8000/api/v1",
                        "KEYCLOAK_ISSUER": f"{ORIGIN}/realms/qualification",
                        "KEYCLOAK_CLIENT_ID": "oligospace-web",
                        "KEYCLOAK_CLIENT_SECRET": client_secret,
                        "NODE_EXTRA_CA_CERTS": "/certs/ca.pem",
                    },
                    "volumes": [ca_mount],
                },
                "caddy": {
                    "image": "caddy:2.11.4-alpine",
                    "volumes": [
                        f"{work / 'Caddyfile'}:/etc/caddy/Caddyfile:ro",
                        f"{work / 'certs'}:/certs:ro",
                    ],
                    "networks": {"default": {"aliases": ["auth-qualification.test"]}},
                },
                "browser": {
                    "build": {
                        "context": str(ROOT),
                        "dockerfile": "infra/docker/web-e2e.Dockerfile",
                    },
                    "command": [
                        "npx",
                        "playwright",
                        "test",
                        "--config",
                        "playwright.oidc.config.ts",
                    ],
                    "environment": {
                        "PLAYWRIGHT_BASE_URL": ORIGIN,
                        "QUALIFICATION_PASSWORD": password,
                        "QUALIFICATION_ADMIN_PASSWORD": admin_password,
                        "QUALIFICATION_IDENTITIES": json.dumps(identities),
                        "NEXTAUTH_SECRET": auth_secret,
                        "NODE_EXTRA_CA_CERTS": "/certs/ca.pem",
                    },
                    "volumes": [ca_mount, f"{work / 'evidence'}:/evidence"],
                },
            },
        }
        config = work / "compose.json"
        config.write_text(json.dumps(compose))
        project = f"oligospace-oidc-{secrets.token_hex(4)}"
        dc = ["docker", "compose", "--project-name", project, "--file", str(config)]
        try:
            print("Building disposable qualification images", flush=True)
            run(dc + ["config", "--quiet"])
            run(dc + ["build", "api", "web", "browser"])
            run(dc + ["up", "--detach", "--wait", "postgres"])
            run(
                dc
                + [
                    "run",
                    "--rm",
                    "api",
                    "micromamba",
                    "run",
                    "--name",
                    "base",
                    "alembic",
                    "upgrade",
                    "head",
                ]
            )
            organization = str(uuid.uuid4())
            sql = f"INSERT INTO organizations(id,name,slug,active) VALUES ('{organization}','Synthetic qualification','qualification',true);\n"
            for role, subject in identities.items():
                if role in ("pending", "mfa"):
                    continue
                db_role = role if role in ("admin", "viewer") else "member"
                sql += f"INSERT INTO users(id,oidc_subject,identity_provider,email,display_name,active,global_role,organization_id) VALUES ('{uuid.uuid4()}','{subject}','keycloak','{role}@qualification.invalid','Synthetic {role.title()}',true,'{db_role}','{organization}');\n"
            run(
                dc
                + [
                    "exec",
                    "-T",
                    "postgres",
                    "psql",
                    "-U",
                    "qualification",
                    "-d",
                    "qualification",
                    "-v",
                    "ON_ERROR_STOP=1",
                ],
                data=sql,
            )
            run(dc + ["up", "--detach", "keycloak", "api", "web", "caddy"])
            print(
                "Running real HTTPS/Keycloak Chromium qualification (credential output suppressed)",
                flush=True,
            )
            browser = subprocess.run(
                dc + ["run", "--rm", "browser"],
                text=True,
                capture_output=True,
                check=False,
            )
            results = []
            for line in browser.stdout.splitlines():
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if (
                    set(item) == {"test", "status"}
                    and isinstance(item["test"], str)
                    and len(item["test"]) < 180
                    and item["status"]
                    in ("passed", "failed", "timedOut", "skipped", "interrupted")
                ):
                    results.append(item)
                    print(json.dumps(item), flush=True)
            passed = (
                browser.returncode == 0
                and len(results) == 12
                and all(item["status"] == "passed" for item in results)
            )
            summary.update(
                qualification="passed" if passed else "failed", tests=results
            )
            (evidence / "summary.json").write_text(json.dumps(summary, indent=2))
            for name in ("synthetic-dashboard.png", "synthetic-administration.png"):
                source = work / "evidence" / name
                if source.exists():
                    shutil.copyfile(source, evidence / name)
            if not passed:
                raise RuntimeError(
                    "Qualification phase failed: browser; inspect sanitized summary.json"
                )
            print(
                json.dumps(
                    {
                        "qualification": "passed",
                        "authentication": "real-keycloak",
                        "transport": "https",
                        "data": "synthetic-only",
                    }
                )
            )
        finally:
            run(dc + ["down", "--volumes", "--remove-orphans"])


if __name__ == "__main__":
    main()
