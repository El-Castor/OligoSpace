"""Disposable, synthetic-only HTTPS/Keycloak qualification. Never reads .env."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import selectors
import secrets
import subprocess
import tempfile
import time
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


TEST_TITLES = (
    "real login enforces PKCE, state, nonce and secure session cookies",
    "a callback with forged state cannot establish a session",
    "administrator provisions a synthetic identity through the real UI",
    "member permissions remain server enforced",
    "viewer permissions remain server enforced",
    "anonymous, malformed and development-header API requests are refused",
    "invalid password does not establish an application session",
    "project membership grant and revocation apply to the same issued token",
    "local account deactivation rejects a still-valid provider token",
    "provider logout failure preserves the session and a confirmed retry revokes it",
    "expired access tokens refresh and logout revokes the provider session",
    "Keycloak account disable rejects an already issued token and failed refresh",
    "provider TOTP enrollment and next-login MFA challenge are enforced",
)


def parse_browser_results(output: str) -> list[dict[str, object]]:
    results = []
    for line in output.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if (
            isinstance(item, dict)
            and set(item) == {"test", "status", "source_line", "rule_id"}
            and isinstance(item["test"], str)
            and item["test"] in TEST_TITLES
            and item["status"]
            in ("passed", "failed", "timedOut", "skipped", "interrupted")
        ):
            if item["rule_id"] not in (
                None,
                "navigation",
                "visibility",
                "equality",
                "timeout",
                "other",
            ) or (
                item["source_line"] is not None
                and not isinstance(item["source_line"], int)
            ):
                continue
            results.append(item)
            print(json.dumps(item), flush=True)
    return results


def collect_evidence(dc: list[str], work: Path, evidence: Path) -> None:
    # Raw API output lives only in this process. Retain counts of fixed
    # warning identifiers; never serialize a line, header or exception.
    api_logs = subprocess.run(
        dc + ["logs", "--no-color", "api"],
        text=True,
        capture_output=True,
        check=False,
    )
    rule_ids = (
        "JWKS_FETCH_FAILED",
        "JWT_SIGNATURE_INVALID",
        "JWT_CLAIMS_INVALID",
        "OIDC_INTROSPECTION_HTTP_FAILED",
        "OIDC_INTROSPECTION_TRANSPORT_FAILED",
        "OIDC_INTROSPECTION_JSON_INVALID",
        "OIDC_INTROSPECTION_INACTIVE",
    )
    rule_counts = {
        rule: len(
            re.findall(
                r"\b" + re.escape(rule) + r"\b",
                api_logs.stdout + api_logs.stderr,
            )
        )
        for rule in rule_ids
    }
    (evidence / "api-rule-counts.json").write_text(json.dumps(rule_counts, indent=2))
    del api_logs
    for name in (
        "synthetic-login.png",
        "synthetic-dashboard.png",
        "synthetic-administration.png",
    ):
        source = work / "evidence" / name
        if source.exists():
            shutil.copyfile(source, evidence / name)
    structure_path = work / "evidence/oidc-structure.json"
    if structure_path.exists():
        structure = json.loads(structure_path.read_text())
        booleans = {
            "has_sub",
            "issuer_expected",
            "audience_expected",
            "realm_roles_present",
        }
        if (
            isinstance(structure, dict)
            and set(structure) == booleans | {"me_status", "me_rule"}
            and all(type(structure[key]) is bool for key in booleans)
            and type(structure["me_status"]) is int
            and 100 <= structure["me_status"] <= 599
            and structure["me_rule"]
            in (
                "invalid_token",
                "account_not_provisioned",
                "identity_provider_mismatch",
                "account_disabled",
                "other",
            )
        ):
            (evidence / "oidc-structure.json").write_text(
                json.dumps(structure, indent=2)
            )
    state_path = work / "evidence/state-probe.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
        if (
            isinstance(state, dict)
            and set(state) == {"interception_seen", "session_present", "path_class"}
            and type(state["interception_seen"]) is bool
            and type(state["session_present"]) is bool
            and state["path_class"] in ("login", "auth", "realms", "other")
        ):
            (evidence / "state-probe.json").write_text(json.dumps(state, indent=2))


def capture_service_logs(command: list[str]) -> tuple[bytes, str | None]:
    """Read complete logs into bounded RAM; an incomplete read never passes."""
    output = bytearray()
    limit = 4 * 1024 * 1024
    deadline = time.monotonic() + 30
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    )
    try:
        assert process.stdout is not None
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                if time.monotonic() >= deadline:
                    return bytes(output), "LOG_RETRIEVAL_TIMEOUT"
                for key, _ in selector.select(timeout=0.5):
                    block = os.read(key.fd, 65536)
                    if not block:
                        selector.unregister(key.fileobj)
                        continue
                    remaining = limit - len(output)
                    output.extend(block[:remaining])
                    if len(block) > remaining:
                        return bytes(output), "LOG_LIMIT_EXCEEDED"
            remaining_time = max(0.1, deadline - time.monotonic())
            if process.wait(timeout=remaining_time) != 0:
                return bytes(output), "LOG_RETRIEVAL_FAILED"
        return bytes(output), None
    except (OSError, subprocess.TimeoutExpired):
        return bytes(output), "LOG_RETRIEVAL_FAILED"
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)
        if process.stdout is not None:
            process.stdout.close()


def check_log_secrets(
    dc: list[str], private_values: dict[str, str], evidence: Path
) -> str:
    """Retain service, fixed rules/categories and counts; never raw log bytes."""
    services = []
    token_pattern = re.compile(
        rb"(?<![A-Za-z0-9_-])[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\."
        rb"[A-Za-z0-9_-]{16,}(?![A-Za-z0-9_-])"
    )
    for service in ("api", "web", "keycloak", "caddy"):
        try:
            logs, retrieval_rule = capture_service_logs(
                dc + ["logs", "--no-color", service]
            )
        except OSError:
            logs, retrieval_rule = b"", "LOG_RETRIEVAL_FAILED"
        findings = []
        for category, value in private_values.items():
            if category not in (
                "identity_password",
                "client_secret",
                "session_secret",
                "database_password",
                "bootstrap_password",
                "storage_access_key",
                "storage_secret_key",
            ):
                category = "other_generated_secret"
            count = logs.count(value.encode()) if value else 0
            if count:
                findings.append(
                    {
                        "rule_id": "GENERATED_SECRET_PRESENT",
                        "category": category,
                        "count": count,
                    }
                )
        token_count = sum(1 for _ in token_pattern.finditer(logs))
        if token_count:
            findings.append(
                {
                    "rule_id": "JWT_LIKE_TOKEN_PRESENT",
                    "category": "jwt_like",
                    "count": token_count,
                }
            )
        if retrieval_rule:
            if retrieval_rule not in (
                "LOG_RETRIEVAL_FAILED",
                "LOG_RETRIEVAL_TIMEOUT",
                "LOG_LIMIT_EXCEEDED",
            ):
                retrieval_rule = "LOG_RETRIEVAL_FAILED"
            findings.append(
                {"rule_id": retrieval_rule, "category": "log_retrieval", "count": 1}
            )
        gate = (
            "failed"
            if any(item["category"] != "log_retrieval" for item in findings)
            else "not_verified"
            if retrieval_rule
            else "passed"
        )
        services.append({"service": service, "gate": gate, "findings": findings})
        del logs
    gate = (
        "failed"
        if any(item["gate"] == "failed" for item in services)
        else "not_verified"
        if any(item["gate"] == "not_verified" for item in services)
        else "passed"
    )
    (evidence / "secret-log-gate.json").write_text(
        json.dumps({"gate": gate, "services": services}, indent=2)
    )
    return gate


def browser_run(
    dc: list[str], *, preflight: bool = False
) -> subprocess.CompletedProcess[str]:
    command = dc + ["run", "--rm", "browser"]
    if preflight:
        command += [
            "npx",
            "playwright",
            "test",
            "--config",
            "playwright.oidc.config.ts",
            "--grep",
            # Playwright matches the complete project/file/title path.
            "(?:^| )real login enforces PKCE",
        ]
    return subprocess.run(command, text=True, capture_output=True, check=False)


def main() -> None:
    os.umask(0o077)
    evidence = ROOT / "infra/auth-qualification/evidence"
    evidence.mkdir(exist_ok=True)
    for name in (
        "synthetic-login.png",
        "synthetic-dashboard.png",
        "synthetic-administration.png",
        "oidc-structure.json",
        "api-rule-counts.json",
        "state-probe.json",
        "secret-log-gate.json",
    ):
        (evidence / name).unlink(missing_ok=True)
    source = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    source_commit = source.stdout.strip()
    if source.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", source_commit):
        source_commit = None
    summary: dict[str, object] = {
        "qualification": "not_completed",
        "source_commit": source_commit,
        "tests": [],
    }
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
        private_values = {
            "identity_password": password,
            "client_secret": client_secret,
            "session_secret": auth_secret,
            "database_password": db_password,
            "bootstrap_password": admin_password,
        }
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
        private_values.update(
            storage_access_key=api_env["OBJECT_STORAGE_ACCESS_KEY"],
            storage_secret_key=api_env["OBJECT_STORAGE_SECRET_KEY"],
        )
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
            preflight = browser_run(dc, preflight=True)
            preflight_results = parse_browser_results(preflight.stdout)
            preflight_passed = (
                preflight.returncode == 0
                and len(preflight_results) == 1
                and preflight_results[0]["test"] == TEST_TITLES[0]
                and preflight_results[0]["status"] == "passed"
            )
            if not preflight_passed:
                results = preflight_results + [
                    {
                        "test": title,
                        "status": "not_executed",
                        "source_line": None,
                        "rule_id": None,
                    }
                    for title in TEST_TITLES[1:]
                ]
                summary.update(qualification="failed", phase="preflight", tests=results)
                (evidence / "summary.json").write_text(json.dumps(summary, indent=2))
                collect_evidence(dc, work, evidence)
                check_log_secrets(dc, private_values, evidence)
                raise RuntimeError(
                    "Qualification phase failed: login preflight; remaining cases not executed"
                )
            print(
                "Login preflight passed; running all thirteen qualification cases",
                flush=True,
            )
            browser = browser_run(dc)
            results = parse_browser_results(browser.stdout)
            passed = (
                browser.returncode == 0
                and len(results) == len(TEST_TITLES)
                and {item["test"] for item in results} == set(TEST_TITLES)
                and all(item["status"] == "passed" for item in results)
            )
            summary.update(
                qualification="passed" if passed else "failed",
                phase="full",
                tests=results,
            )
            (evidence / "summary.json").write_text(json.dumps(summary, indent=2))
            collect_evidence(dc, work, evidence)
            log_gate = check_log_secrets(dc, private_values, evidence)
            if log_gate != "passed":
                passed = False
                summary.update(qualification="failed", log_gate=log_gate)
                (evidence / "summary.json").write_text(json.dumps(summary, indent=2))
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
