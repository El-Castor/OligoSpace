"""Synthetic-only native disaster-recovery qualification; never an installer.

Two generated Compose projects, fresh project-scoped volumes, real PostgreSQL,
Keycloak backed by PostgreSQL, API, Redis, worker and a disposable S3 candidate.
Only generated loopback ports are published. No production configuration is read.
Credentials, tokens, SQL contents and command output never enter the report.
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import UTC, datetime
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import platform
import re
import secrets
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
from unittest.mock import patch

from minio import Minio

from recovery import Recovery

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra/deployment"))
from storage_profiles import IMAGES, command, prepare  # noqa: E402

ISSUER = "http://keycloak:8080/realms/recovery"
DATABASES = {
    "application": {"name": "oligospace", "user": "recovery"},
    "identity": {"name": "keycloak", "user": "recovery"},
}
WRITERS = ["api", "bioinfo-worker", "scientific-scheduler", "keycloak"]
CORPUS = {
    "quarantine/ADN + 100%#?.txt": (b"ATGCGTACGTTAGCGTACGA\n", "text/plain"),
    "quarantine/échantillon β.bin": (bytes(range(256)) * 8, "application/octet-stream"),
    "empty": (b"", "application/octet-stream"),
}


class QualificationError(RuntimeError):
    """Only fixed harness rule IDs may enter sanitized evidence."""

    def __init__(self, rule, *, diagnostic=None):
        super().__init__(rule)
        self.diagnostic = diagnostic


def require(value: bool, rule: str) -> None:
    if not value:
        raise QualificationError(rule)


def execute(args: list[str], data: bytes | None = None, *, merge_stderr=False) -> bytes:
    result = subprocess.run(
        args,
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT if merge_stderr else subprocess.PIPE,
        timeout=1800,
        check=False,
    )
    if result.returncode:
        # No subprocess body/URL/password is copied into a failure message.
        output = result.stdout + (result.stderr or b"")
        diagnostic = {
            "command_phase": next(
                (
                    item
                    for item in args
                    if item
                    in (
                        "build",
                        "run",
                        "up",
                        "exec",
                        "down",
                        "config",
                        "logs",
                        "inspect",
                    )
                ),
                "other",
            ),
            "categories": [
                name
                for name, pattern in {
                    "permission": rb"permission denied",
                    "build": rb"failed to solve",
                    "registry": rb"failed to fetch|manifest unknown|pull access denied",
                    "dns": rb"could not resolve|temporary failure resolving|name or service not known",
                    "network": rb"connection refused|network is unreachable|connection timed out|TLS handshake timeout",
                    "certificate": rb"certificate verify failed|certificate verification failed|x509:",
                    "apt_index": rb"Unable to locate package|does not have a Release file|Some index files failed",
                    "apt_integrity": rb"Hash Sum mismatch|signatures couldn't be verified|NO_PUBKEY",
                    "capacity": rb"no space left on device|disk quota exceeded",
                    "database": rb"ERROR:|FATAL:",
                    "missing_file": rb"no such file or directory",
                }.items()
                if re.search(pattern, output, flags=re.IGNORECASE)
            ],
        }
        raise QualificationError("qualification_command_failed", diagnostic=diagnostic)
    return result.stdout


def wait_for(action, *, seconds=180):
    deadline = time.monotonic() + seconds
    while True:
        try:
            return action()
        except Exception:
            if time.monotonic() >= deadline:
                raise QualificationError("qualification_readiness_timeout") from None
            time.sleep(2)


def http(url, *, form=None, body=None, token=None, method=None):
    headers = {}
    payload = None
    if form is not None:
        payload = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if body is not None:
        payload = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, data=payload, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = response.read()
            return response.status, json.loads(data) if data else None
    except urllib.error.HTTPError as error:
        return error.code, None


class Stack:
    def __init__(
        self, root: Path, context: str, side: str, values: dict, identities: dict
    ):
        self.root = root / side
        self.root.mkdir(mode=0o700)
        self.project = "oligospace-deploy04-test-" + side + "-" + secrets.token_hex(5)
        self.context = context
        self.values = values
        self.identities = identities
        self.compose_file = self.root / "compose.json"
        self.env_file = self.root / "empty.env"
        self.env_file.write_text("")
        self.env_file.chmod(0o600)
        self.config = None
        self.api = self.kc = ""
        self.client = None
        self.started = False
        self.make_compose(side == "source")

    def dc(self, *args, data=None):
        return execute(
            [
                "docker",
                "--context",
                self.context,
                "compose",
                "--project-name",
                self.project,
                "--file",
                str(self.compose_file),
                "--env-file",
                str(self.env_file),
                *args,
            ],
            data,
            merge_stderr=bool(args and args[0] == "logs"),
        )

    def sql(self, query, database="oligospace"):
        return (
            self.dc(
                "exec",
                "-T",
                "postgres",
                "psql",
                "-X",
                "-U",
                "recovery",
                "-d",
                database,
                "-At",
                "-v",
                "ON_ERROR_STOP=1",
                data=query.encode(),
            )
            .decode()
            .strip()
        )

    def make_compose(self, source):
        values = self.values
        storage = prepare(
            "garage",
            self.project + "-s3",
            self.root,
            values["storage_access"],
            values["storage_secret"],
        )
        self.storage_secrets = storage["extra_secret_values"]
        api_env = {
            "ENVIRONMENT": "production",
            "AUTH_MODE": "oidc",
            "UPLOADS_ENABLED": "false",
            "DATABASE_URL": f"postgresql+asyncpg://os_app:{values['app_database']}@postgres:5432/oligospace",
            "REDIS_URL": "redis://redis:6379/0",
            "OIDC_ISSUER": ISSUER,
            "OIDC_AUDIENCE": "oligospace-api",
            "OIDC_CLIENT_ID": "oligospace-web",
            "OIDC_CLIENT_SECRET": values["client"],
            "OBJECT_STORAGE_ACCESS_KEY": values["storage_access"],
            "OBJECT_STORAGE_SECRET_KEY": values["storage_secret"],
            "OBJECT_STORAGE_ENDPOINT": "s3:3900",
        }
        kc = {
            "image": "quay.io/keycloak/keycloak:26.7.2",
            "command": ["start-dev"] + (["--import-realm"] if source else []),
            "environment": {
                "KC_DB": "postgres",
                "KC_DB_URL": "jdbc:postgresql://postgres:5432/keycloak",
                "KC_DB_USERNAME": "os_identity",
                "KC_DB_PASSWORD": values["identity_database"],
                "KC_HOSTNAME": "http://keycloak:8080",
                "KC_HTTP_ENABLED": "true",
                "KC_BOOTSTRAP_ADMIN_USERNAME": "synthetic-bootstrap",
                "KC_BOOTSTRAP_ADMIN_PASSWORD": values["bootstrap"],
            },
            "ports": ["127.0.0.1::8080"],
        }
        if source:
            realm = json.loads(
                (ROOT / "infra/keycloak/realm-oligospace.json").read_text()
            )
            realm.update(
                realm="recovery",
                sslRequired="none",
                resetPasswordAllowed=False,
                rememberMe=False,
                accessTokenLifespan=300,
            )
            realm["clients"][0].update(
                secret=values["client"],
                redirectUris=["http://unused.invalid/callback"],
                webOrigins=[],
                directAccessGrantsEnabled=True,
            )
            realm["users"] = [
                {
                    "id": subject,
                    "username": "synthetic-" + persona,
                    "email": persona + "@recovery.invalid",
                    "firstName": "Synthetic",
                    "lastName": persona.title(),
                    "enabled": True,
                    "emailVerified": True,
                    "credentials": [
                        {
                            "type": "password",
                            "value": values["password"],
                            "temporary": False,
                        }
                    ],
                    "realmRoles": ["admin" if persona == "admin" else "viewer"],
                }
                for persona, subject in self.identities.items()
            ]
            realm_file = self.root / "realm.json"
            realm_file.write_text(json.dumps(realm))
            realm_file.chmod(0o644)
            # Only synthetic temporary directories are traversable by Keycloak UID1000.
            self.root.chmod(0o755)
            kc["volumes"] = [f"{realm_file}:/opt/keycloak/data/import/recovery.json:ro"]
        compose = {
            "networks": {
                "default": {"internal": True},
                # Docker does not publish ports on an internal-only bridge.
                # Only host-operated HTTP/S3 qualification endpoints join this
                # second bridge; DB/cache/worker remain on the internal network.
                "qualification_ingress": {
                    "driver": "bridge",
                    "driver_opts": {
                        "com.docker.network.bridge.host_binding_ipv4": "127.0.0.1"
                    },
                },
            },
            "volumes": {"postgres": {}, "objects": {}},
            "services": {
                "postgres": {
                    "image": "postgres:17.11-alpine",
                    "environment": {
                        "POSTGRES_USER": "recovery",
                        "POSTGRES_PASSWORD": values["database"],
                        "POSTGRES_DB": "oligospace",
                    },
                    "volumes": ["postgres:/var/lib/postgresql/data"],
                    "healthcheck": {
                        "test": [
                            "CMD",
                            "pg_isready",
                            "-U",
                            "recovery",
                            "-d",
                            "oligospace",
                        ],
                        "interval": "2s",
                        "retries": 90,
                    },
                },
                "keycloak": kc,
                "redis": {"image": "redis:7.4.10-alpine", "tmpfs": ["/data"]},
                "s3": {
                    "image": IMAGES["garage"],
                    "command": command("garage", self.project + "-s3"),
                    "environment": storage["environment"],
                    "volumes": [
                        "objects:/data",
                        f"{self.root / 'garage.toml'}:/etc/garage.toml:ro",
                    ],
                    "ports": ["127.0.0.1::3900"],
                },
                "api": {
                    "image": "oligospace-deploy04-api:test",
                    "build": {
                        "context": str(ROOT),
                        "dockerfile": "infra/docker/api/Dockerfile",
                    },
                    "environment": api_env,
                    "ports": ["127.0.0.1::8000"],
                    "command": [
                        "uvicorn",
                        "oligospace_api.main:app",
                        "--host",
                        "0.0.0.0",
                        "--port",
                        "8000",
                    ],
                },
                "bioinfo-worker": {
                    "image": "oligospace-deploy04-worker:test",
                    "build": {
                        "context": str(ROOT),
                        "dockerfile": "infra/docker/bioinfo-worker.Dockerfile",
                    },
                    "environment": {
                        "DATABASE_URL": f"postgresql+asyncpg://os_worker:{values['worker_database']}@postgres:5432/oligospace",
                        "REDIS_URL": api_env["REDIS_URL"],
                    },
                },
                "scientific-scheduler": {
                    "image": "oligospace-deploy04-worker:test",
                    "environment": {
                        "DATABASE_URL": f"postgresql+asyncpg://os_worker:{values['worker_database']}@postgres:5432/oligospace",
                        "REDIS_URL": api_env["REDIS_URL"],
                    },
                    "command": [
                        "celery",
                        "--app",
                        "oligospace_bioinfo.celery_app:app",
                        "beat",
                        "--loglevel=INFO",
                        "--schedule=/tmp/celerybeat",
                        "--pidfile=/tmp/beat.pid",
                    ],
                },
            },
        }
        for name in ("api", "keycloak", "s3"):
            compose["services"][name]["networks"] = ["default", "qualification_ingress"]
        # Reuse the proven non-root/read-only API/worker runtime constraints.
        spec = importlib.util.spec_from_file_location(
            "auth_qualification", ROOT / "infra/auth-qualification/run.py"
        )
        auth = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(auth)
        auth.harden_compose(compose)
        self.compose_file.write_text(json.dumps(compose))
        self.compose_file.chmod(0o600)

    def start_data(self, *, build=False):
        self.dc("config", "--quiet")
        if build:
            self.dc("build", "api", "bioinfo-worker")
        self.started = True
        self.dc("up", "--detach", "--wait", "postgres", "redis", "s3")
        self.sql(
            f"CREATE ROLE os_app LOGIN PASSWORD '{self.values['app_database']}';"
            f"CREATE ROLE os_worker LOGIN PASSWORD '{self.values['worker_database']}';"
            f"CREATE ROLE os_identity LOGIN PASSWORD '{self.values['identity_database']}';",
            "postgres",
        )
        self.sql("CREATE DATABASE keycloak OWNER os_identity;", "postgres")
        endpoint = self.dc("port", "s3", "3900").decode().strip()
        require(
            bool(re.fullmatch(r"127\.0\.0\.1:\d+", endpoint)),
            "loopback_storage_required",
        )
        self.client = Minio(
            endpoint,
            access_key=self.values["storage_access"],
            secret_key=self.values["storage_secret"],
            secure=False,
        )
        wait_for(self.client.list_buckets)
        self.config = {
            "context": self.context,
            "project": self.project,
            "compose_file": str(self.compose_file),
            "env_file": str(self.env_file),
            "database_service": "postgres",
            "databases": DATABASES,
            "writers": WRITERS,
            "non_writers": ["postgres", "redis", "s3"],
            "state_dir": str(self.root / "state"),
            "external_writers_excluded": True,
            "buckets": ["recovery-evidence"],
            "s3": {
                "endpoint": endpoint,
                "access_key": self.values["storage_access"],
                "secret_key": self.values["storage_secret"],
                "secure": False,
            },
            "source_revision": execute(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
            .decode()
            .strip(),
            "configuration_files": [
                str(ROOT / "infra/deployment/configuration.env.example")
            ],
            "secret_inventory": [
                "DATABASE_PASSWORD",
                "APP_DATABASE_PASSWORD",
                "WORKER_DATABASE_PASSWORD",
                "IDENTITY_DATABASE_PASSWORD",
                "OIDC_CLIENT_SECRET",
                "OIDC_USER_CREDENTIALS",
                "STORAGE_CREDENTIALS",
                "BACKUP_ENCRYPTION_KEY",
            ],
        }

    def migrate(self):
        # Keep the temporary bootstrap URL out of argv and the runtime API env.
        override = self.root / "migration.json"
        override.write_text(
            json.dumps(
                {
                    "services": {
                        "api": {
                            "environment": {
                                "DATABASE_URL": f"postgresql+asyncpg://recovery:{self.values['database']}@postgres:5432/oligospace"
                            }
                        }
                    }
                }
            )
        )
        override.chmod(0o600)
        try:
            self.dc(
                "--file",
                str(override),
                "run",
                "--rm",
                "--no-deps",
                "api",
                "/opt/venv/bin/python",
                "-m",
                "alembic",
                "upgrade",
                "head",
            )
        finally:
            override.unlink(missing_ok=True)
        # Match the existing disposable bootstrap's production role boundaries.
        self.sql("""
            REVOKE CREATE ON SCHEMA public FROM PUBLIC;
            GRANT CONNECT ON DATABASE oligospace TO os_app, os_worker;
            GRANT USAGE ON SCHEMA public TO os_app, os_worker;
            GRANT SELECT,INSERT,UPDATE,DELETE ON ALL TABLES IN SCHEMA public TO os_app;
            GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA public TO os_app;
            GRANT SELECT,INSERT,UPDATE ON scientific_jobs,scientific_job_attempts,scientific_job_results TO os_worker;
            GRANT INSERT ON audit_events TO os_worker;
        """)

    def start_writers(self):
        self.dc("up", "--detach", *WRITERS)
        self.api = (
            "http://" + self.dc("port", "api", "8000").decode().strip() + "/api/v1"
        )
        self.kc = "http://" + self.dc("port", "keycloak", "8080").decode().strip()

        def ready():
            status, _ = http(
                self.kc + "/realms/recovery/.well-known/openid-configuration"
            )
            require(status == 200, "keycloak_not_ready")
            status, _ = http(self.api + "/health/live")
            require(status == 200, "api_not_ready")

        wait_for(ready, seconds=240)

    def token(self, persona):
        status, value = http(
            self.kc + "/realms/recovery/protocol/openid-connect/token",
            form={
                "grant_type": "password",
                "client_id": "oligospace-web",
                "client_secret": self.values["client"],
                "username": "synthetic-" + persona,
                "password": self.values["password"],
                "scope": "openid",
            },
        )
        require(
            status == 200 and isinstance(value, dict) and "access_token" in value,
            "oidc_login_failed",
        )
        return value["access_token"]

    def call(self, token, path, *, body=None, expected=200, method=None):
        status, result = http(self.api + path, token=token, body=body, method=method)
        require(status == expected, "api_contract_failed")
        return result

    def stop(self):
        if self.started:
            # No --volumes: project-scoped volumes remain available for controlled inspection.
            self.dc("down", "--remove-orphans", "--timeout", "30")
            self.started = False


def seed(stack: Stack):
    organization, admin, viewer = (str(uuid.uuid4()) for _ in range(3))
    stack.sql(f"""
      INSERT INTO organizations(id,name,slug,active)
        VALUES ('{organization}','Synthetic recovery laboratory','synthetic-recovery',true);
      INSERT INTO users(id,oidc_subject,identity_provider,email,display_name,active,global_role,organization_id)
        VALUES ('{admin}','{stack.identities["admin"]}','keycloak','admin@recovery.invalid','Synthetic admin',true,'admin','{organization}'),
        ('{viewer}','{stack.identities["viewer"]}','keycloak','viewer@recovery.invalid','Synthetic viewer',true,'viewer','{organization}');
    """)
    return organization, admin, viewer


def science(stack: Stack, token: str, oligo: str, *, golden=False):
    job = stack.call(
        token,
        "/scientific-jobs/oligo-primer3-qc",
        body={"oligo_public_id": oligo},
        expected=202,
    )
    public_id = job["public_id"]

    def completed():
        current = stack.call(token, "/scientific-jobs/" + public_id)
        require(current["state"] == "succeeded", "scientific_job_not_succeeded")
        return current

    result = wait_for(completed)
    require(result["result"]["tool_version"] == "2.6.1", "scientific_version_changed")
    require(
        result["result"]["tool_source_sha256"]
        == "805cef7ef39607cd40f0f5bb8b32e35e20007153a0a55131dd430ce644c8fb9e",
        "scientific_source_changed",
    )
    require(
        result["attempts"] and result["attempts"][-1]["state"] == "succeeded",
        "scientific_attempt_missing",
    )
    if golden:
        for name, value in {
            "nearest_neighbor_tm": 59.62663,
            "hairpin": 69.836183,
            "homodimer": 46.16876,
        }.items():
            fact = result["result"]["payload"][name]
            require(
                fact["state"] == "available" and abs(fact["value"] - value) <= 1e-6,
                "scientific_golden_value_changed",
            )
    return result


def create_records(stack: Stack, organization: str, admin: str):
    token = stack.token("admin")
    me = stack.call(token, "/me")
    require(me["id"] == admin, "identity_mapping_failed")
    team = stack.call(
        token,
        "/workspace/teams",
        body={"name": "Synthetic recovery team"},
        expected=201,
    )
    project = stack.call(
        token,
        "/workspace/projects",
        body={
            "name": "Synthetic recovery project",
            "team_id": team["id"],
            "visibility": "organization",
        },
        expected=201,
    )
    target = stack.call(
        token,
        "/registry/targets",
        body={
            "name": "Synthetic recovery target",
            "owner_project_id": project["id"],
            "visibility": "organization",
            "reference_sequence": "ATGCGTACGTTAGCGTACGA",
        },
        expected=201,
    )
    oligo = stack.call(
        token,
        "/registry/oligos",
        body={
            "name": "Synthetic recovery oligo",
            "sequence": "ATGCGTACGTTAGCGTACGA",
            "owner_project_id": project["id"],
            "visibility": "organization",
        },
        expected=201,
    )["oligo"]
    kind = stack.call(
        token,
        "/registry/experiment-types",
        body={
            "name": "Recovery PCR",
            "slug": "recovery-pcr",
            "allowed_roles": ["forward_primer", "reverse_primer"],
        },
        expected=201,
    )
    assay = stack.call(
        token,
        "/registry/assays",
        body={
            "name": "Synthetic recovery assay",
            "experiment_type_id": kind["id"],
            "target_id": target["id"],
            "project_id": project["id"],
            "visibility": "organization",
            "oligos": [{"oligo_id": oligo["id"], "role": "forward_primer"}],
        },
        expected=201,
    )
    job = science(stack, token, oligo["public_id"], golden=True)
    stack.client.make_bucket("recovery-evidence")
    for key, (body, content_type) in CORPUS.items():
        stack.client.put_object(
            "recovery-evidence",
            key,
            io.BytesIO(body),
            len(body),
            content_type=content_type,
            metadata={"origin": "synthetic-deploy04", "visibility": "quarantined"},
        )
    key = next(iter(CORPUS))
    body, content_type = CORPUS[key]
    run_id = str(uuid.uuid4())
    stack.sql(f"""
      INSERT INTO experiment_runs(id,organization_id,public_id,assay_id,assay_version,project_id,operator_id,performed_at,conditions,input_metadata,visibility,status,created_by_id,updated_by_id)
      VALUES ('{run_id}','{organization}','EXP-900001','{assay["id"]}',{assay["version"]},'{project["id"]}','{admin}',now(),'{{}}','{{"fixture":"direct-synthetic-SQL-no-upload"}}','organization','active','{admin}','{admin}');
      INSERT INTO attachments(id,organization_id,public_id,experiment_run_id,object_key,original_filename,content_type,size_bytes,sha256,uploaded_by_id,scan_status,publication_status)
      VALUES (gen_random_uuid(),'{organization}','ATT-900001','{run_id}','{key}','synthetic.txt','{content_type}',{len(body)},'{hashlib.sha256(body).hexdigest()}','{admin}','pending','quarantined');
    """)
    viewer = stack.token("viewer")
    stack.call(viewer, "/registry/oligos/" + oligo["public_id"])
    stack.call(
        viewer,
        "/registry/oligos",
        body={"name": "Forbidden", "sequence": "ACGT"},
        expected=403,
    )
    stack.call(
        viewer,
        "/scientific-jobs/oligo-primer3-qc",
        body={"oligo_public_id": oligo["public_id"]},
        expected=403,
    )
    return {
        "project": project,
        "target": target,
        "oligo": oligo,
        "assay": assay,
        "job": job,
    }


def fingerprint(stack: Stack, *, database="oligospace", tables=None):
    if tables is None:
        tables = stack.sql(
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;",
            database,
        ).splitlines()
    result = {}
    for table in tables:
        require(
            bool(re.fullmatch(r"[a-z_][a-z0-9_]*", table)), "unsafe_table_identifier"
        )
        # Sorted JSON captures every value, UUID, relationship and provenance field.
        rows = stack.sql(
            f"SELECT coalesce(jsonb_agg(row ORDER BY row::text),'[]'::jsonb) FROM (SELECT to_jsonb(t) AS row FROM \"{table}\" t) r;",
            database,
        )
        result[table] = hashlib.sha256(rows.encode()).hexdigest()
    return result


def verify_objects(stack: Stack):
    require(
        {
            item.object_name
            for item in stack.client.list_objects("recovery-evidence", recursive=True)
        }
        == set(CORPUS),
        "object_set_changed",
    )
    for key, (body, content_type) in CORPUS.items():
        response = stack.client.get_object("recovery-evidence", key)
        try:
            require(response.read() == body, "object_bytes_changed")
        finally:
            response.close()
            response.release_conn()
        stat = stack.client.stat_object("recovery-evidence", key)
        require(stat.content_type == content_type, "object_content_type_changed")
        metadata = {k.lower(): v for k, v in stat.metadata.items()}
        require(
            metadata.get("x-amz-meta-origin") == "synthetic-deploy04",
            "object_metadata_changed",
        )


def verify_runtime_grants(stack: Stack):
    require(
        stack.sql("""SELECT
          has_table_privilege('os_app','oligos','INSERT') AND
          has_table_privilege('os_app','oligos','UPDATE') AND
          has_table_privilege('os_worker','scientific_jobs','SELECT') AND
          has_table_privilege('os_worker','scientific_jobs','INSERT') AND
          has_table_privilege('os_worker','scientific_jobs','UPDATE') AND
          has_table_privilege('os_worker','audit_events','INSERT') AND
          NOT has_table_privilege('os_worker','oligos','UPDATE') AND
          NOT has_table_privilege('os_worker','scientific_jobs','DELETE') AND
          NOT has_schema_privilege('os_app','public','CREATE') AND
          NOT has_schema_privilege('os_worker','public','CREATE');""")
        == "t",
        "runtime_grants_not_preserved",
    )


def expect_failure(action, rule):
    try:
        action()
    except Exception:
        return {"case": rule, "status": "passed"}
    raise QualificationError("negative_case_did_not_refuse_" + rule)


def negative_archive_cases(work: Path, backup: Path, key: Path, target: Stack):
    import archive

    tests = []
    corrupt = work / "corrupt.osbk"
    blob = bytearray(backup.read_bytes())
    blob[len(blob) // 2] ^= 1
    corrupt.write_bytes(blob)
    tests.append(
        expect_failure(
            lambda: Recovery(target.config).restore(corrupt, key), "corrupt_archive"
        )
    )
    truncated = work / "truncated.osbk"
    truncated.write_bytes(backup.read_bytes()[:32])
    tests.append(
        expect_failure(
            lambda: Recovery(target.config).restore(truncated, key),
            "incomplete_archive",
        )
    )
    wrong_key = work / "wrong.key"
    wrong_key.write_bytes(secrets.token_bytes(32))
    wrong_key.chmod(0o600)
    tests.append(
        expect_failure(
            lambda: Recovery(target.config).restore(backup, wrong_key),
            "wrong_encryption_key",
        )
    )
    tests.append(
        expect_failure(
            lambda: Recovery(target.config).restore(backup, work / "absent.key"),
            "absent_secrets",
        )
    )
    incomplete_tree = work / "missing-database"
    archive.unseal(backup, incomplete_tree, key)
    incomplete_manifest = json.loads((incomplete_tree / "manifest.json").read_text())
    (incomplete_tree / "identity.dump").unlink()
    incomplete_manifest["files"] = archive.manifest_files(incomplete_tree)
    (incomplete_tree / "manifest.json").write_text(json.dumps(incomplete_manifest))
    incomplete = work / "missing-database.osbk"
    archive.seal(incomplete_tree, incomplete, key)
    tests.append(
        expect_failure(
            lambda: Recovery(target.config).restore(incomplete, key),
            "missing_identity_database",
        )
    )
    tree = work / "missing-object"
    archive.unseal(backup, tree, key)
    manifest = json.loads((tree / "manifest.json").read_text())
    candidates = [
        p
        for p in tree.rglob("*")
        if p.is_file()
        and p.name != "manifest.json"
        and "object" in str(p.relative_to(tree))
    ]
    require(bool(candidates), "negative_object_fixture_missing")
    candidates[0].unlink()
    # Re-sign a complete outer manifest while leaving the inner S3 reference broken.
    # This proves semantic completeness, not merely the AES/outer checksum gate.
    manifest["files"] = archive.manifest_files(tree)
    (tree / "manifest.json").write_text(json.dumps(manifest))
    malformed = work / "missing-object.osbk"
    archive.seal(tree, malformed, key)
    tests.append(
        expect_failure(
            lambda: Recovery(target.config).restore(malformed, key), "missing_object"
        )
    )
    omitted = work / "omitted-reference-object"
    archive.unseal(backup, omitted, key)
    omit_referenced_object(omitted)
    consistent_omission = work / "consistent-omission.osbk"
    archive.seal(omitted, consistent_omission, key)
    tests.append(
        expect_failure(
            lambda: Recovery(target.config).restore(consistent_omission, key),
            "referenced_object_consistently_omitted",
        )
    )
    require(
        target.sql("SELECT count(*) FROM pg_tables WHERE schemaname='public';") == "0",
        "negative_preflight_mutated_database",
    )
    require(not target.client.list_buckets(), "negative_preflight_mutated_objects")
    # A target containing only a function has no rows or tables, but is not empty.
    # The marker is created/deleted solely in this new synthetic qualification DB.
    target.sql(
        "CREATE FUNCTION public.existing_recovery_marker() RETURNS integer LANGUAGE sql IMMUTABLE AS 'SELECT 42';"
    )
    try:
        tests.append(
            expect_failure(
                lambda: Recovery(target.config).restore(backup, key),
                "function_only_target",
            )
        )
        require(
            target.sql("SELECT public.existing_recovery_marker();") == "42",
            "existing_function_modified",
        )
        require(
            target.sql("SELECT count(*) FROM pg_tables WHERE schemaname='public';")
            == "0",
            "function_target_mutated",
        )
        require(not target.client.list_buckets(), "function_target_objects_mutated")
        require(
            not (
                Path(target.config["state_dir"]) / "restore-in-progress.json"
            ).exists(),
            "function_target_restore_started",
        )
    finally:
        target.sql("DROP FUNCTION public.existing_recovery_marker();")
    return tests


def omit_referenced_object(tree: Path):
    """Construct an authenticated-but-semantically-incomplete negative fixture."""
    import archive

    manifest = json.loads((tree / "manifest.json").read_text())
    require(
        bool(manifest.get("attachment_references")),
        "negative_attachment_fixture_missing",
    )
    key = manifest["attachment_references"][0]["object_key"]
    removed = 0
    for bucket in manifest["buckets"]:
        for entry in list(bucket["objects"]):
            if entry["key"] == key:
                (tree / entry["file"]).unlink()
                bucket["objects"].remove(entry)
                removed += 1
    require(removed == 1, "negative_attachment_object_not_unique")
    # The database attachment reference stays present. Both the S3 index and
    # outer checksums are otherwise consistent; only cross-store verification
    # can detect the omission before the first database import.
    manifest["files"] = archive.manifest_files(tree)
    (tree / "manifest.json").write_text(json.dumps(manifest))


def qualification(context: str, report: dict):
    endpoint = json.loads(
        execute(["docker", "--context", context, "context", "inspect", context])
    )[0]["Endpoints"]["docker"]["Host"]
    require(
        endpoint.startswith("unix://") and not os.environ.get("DOCKER_HOST"),
        "explicit_local_engine_required",
    )
    values = {
        name: secrets.token_hex(24)
        for name in (
            "database",
            "app_database",
            "worker_database",
            "identity_database",
            "password",
            "client",
            "bootstrap",
            "storage_access",
            "storage_secret",
        )
    }
    identities = {name: str(uuid.uuid4()) for name in ("admin", "viewer")}
    with (
        tempfile.TemporaryDirectory(prefix="oligospace-deploy04-") as temporary,
        ExitStack() as cleanup,
    ):
        work = Path(temporary)
        work.chmod(0o755)
        key = work / "backup.key"
        key.write_bytes(secrets.token_bytes(32))
        key.chmod(0o600)
        source = Stack(work, context, "source", values, identities)
        target = Stack(work, context, "target", values, identities)
        cleanup.callback(source.stop)
        cleanup.callback(target.stop)
        source.start_data(build=True)
        source.migrate()
        verify_runtime_grants(source)
        organization, admin, _ = seed(source)
        source.start_writers()
        records = create_records(source, organization, admin)
        report["stages"].append("synthetic_data_science_oidc_and_permissions")
        # Stable baseline while all controlled writers are stopped, then restart
        # before invoking the real backup so its pause/resume path is exercised.
        source.dc("stop", "--timeout", "30", *WRITERS)
        before = fingerprint(source)
        identity_tables = [
            "realm",
            "client",
            "user_entity",
            "credential",
            "user_role_mapping",
            "client_scope",
            "protocol_mapper",
            "keycloak_role",
        ]
        identity_before = fingerprint(
            source, database="keycloak", tables=identity_tables
        )
        source.dc("start", *WRITERS)
        source.start_writers()
        archive_path = work / "full.osbk"
        start = time.monotonic()
        manifest = Recovery(source.config).backup(archive_path, key)
        report["backup_seconds"] = round(time.monotonic() - start, 3)
        running = (
            source.dc("ps", "--status", "running", "--services").decode().splitlines()
        )
        require(set(WRITERS).issubset(running), "source_writers_not_resumed")
        report["stages"].append("coordinated_encrypted_backup_and_source_resume")
        target.start_data()
        report["negative_tests"] = negative_archive_cases(
            work, archive_path, key, target
        )
        start = time.monotonic()
        Recovery(target.config).restore(archive_path, key)
        report["restore_seconds"] = round(time.monotonic() - start, 3)
        after = fingerprint(target)
        # Source restart before backup does not authenticate any user or mutate
        # scientific data; compare every application row, including timestamps.
        require(before == after, "application_rows_not_identical")
        require(
            identity_before
            == fingerprint(target, database="keycloak", tables=identity_tables),
            "identity_rows_not_identical",
        )
        verify_objects(target)
        verify_runtime_grants(target)
        report["application_tables_compared"] = len(after)
        report["identity_tables_compared"] = len(identity_tables)
        report["objects_compared"] = len(CORPUS)
        report["runtime_role_permissions"] = (
            "api_dml_worker_bounded_and_schema_create_denied"
        )
        report["stages"].append("empty_target_restore_all_rows_identity_and_objects")
        report["negative_tests"].append(
            expect_failure(
                lambda: Recovery(target.config).restore(archive_path, key),
                "nonempty_target",
            )
        )
        target.start_writers()
        token = target.token("admin")
        require(
            target.call(token, "/me")["id"] == admin, "restored_subject_mapping_failed"
        )
        restored_job = target.call(
            token, "/scientific-jobs/" + records["job"]["public_id"]
        )
        require(
            restored_job == records["job"], "restored_scientific_provenance_changed"
        )
        for kind, path in (
            ("project", "/workspace/projects/"),
            ("target", "/registry/targets/"),
            ("oligo", "/registry/oligos/"),
            ("assay", "/registry/assays/"),
        ):
            require(
                target.call(token, path + records[kind]["public_id"])["id"]
                == records[kind]["id"],
                "restored_resource_identity_changed",
            )
        viewer = target.token("viewer")
        target.call(viewer, "/registry/oligos/" + records["oligo"]["public_id"])
        target.call(
            viewer,
            "/registry/oligos",
            body={"name": "Forbidden", "sequence": "ACGT"},
            expected=403,
        )
        target.call(
            viewer,
            "/scientific-jobs/oligo-primer3-qc",
            body={"oligo_public_id": records["oligo"]["public_id"]},
            expected=403,
        )
        # Fresh UUID/sequence produces an independent real worker computation.
        new = target.call(
            token,
            "/registry/oligos",
            body={
                "name": "Post-recovery worker proof",
                "sequence": "ACGTACGTCGATCGTAGCTAGCTAG",
                "visibility": "organization",
            },
            expected=201,
        )["oligo"]
        science(target, token, new["public_id"])
        report["stages"].append("fresh_oidc_permissions_api_and_worker_after_recovery")
        # Interrupted restore uses a third fresh target. Never retry/erase its data.
        interrupted = Stack(work, context, "interrupted", values, identities)
        cleanup.callback(interrupted.stop)
        interrupted.start_data()
        original = Recovery._restore_database

        def interrupt(self, role, dump):
            if role == "identity":
                raise QualificationError("synthetic_interruption")
            return original(self, role, dump)

        with patch.object(Recovery, "_restore_database", interrupt):
            report["negative_tests"].append(
                expect_failure(
                    lambda: Recovery(interrupted.config).restore(archive_path, key),
                    "interrupted_restore",
                )
            )
        require(
            (
                Path(interrupted.config["state_dir"]) / "restore-in-progress.json"
            ).is_file(),
            "interrupted_restore_marker_missing",
        )
        require(
            interrupted.sql("SELECT count(*) FROM oligos;") == "1"
            and interrupted.sql(
                "SELECT count(*) FROM pg_tables WHERE schemaname='public';", "keycloak"
            )
            == "0",
            "interruption_not_at_expected_restore_boundary",
        )
        report["negative_tests"].append(
            expect_failure(
                lambda: Recovery(interrupted.config).restore(archive_path, key),
                "interrupted_retry_refused",
            )
        )
        running = (
            interrupted.dc("ps", "--status", "running", "--services")
            .decode()
            .splitlines()
        )
        require(
            not set(WRITERS).intersection(running), "interrupted_target_started_writers"
        )
        # The log gate reads all streams into RAM and checks each generated secret.
        # Failed retrieval fails qualification rather than implying absent secrets.
        for stack in (source, target, interrupted):
            logs = stack.dc("logs", "--no-color")
            forbidden = [
                *values.values(),
                *source.storage_secrets,
                *target.storage_secrets,
                *interrupted.storage_secrets,
            ]
            require(
                not any(value.encode() in logs for value in forbidden),
                "generated_secret_present_in_logs",
            )
            require(
                not re.search(
                    rb"\b[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\.[A-Za-z0-9_-]{16,}\b",
                    logs,
                ),
                "jwt_present_in_logs",
            )
        report["secret_log_gate"] = "passed"
        report["stages"].append("negative_fail_closed_and_secret_log_gate")
        report["encrypted_archive_bytes"] = archive_path.stat().st_size
        report["backup_source_resumed"] = manifest.get("source_resumed")
        report["retained_volumes"] = (
            "only unique qualification volumes; no volume deletion"
        )
        report["limitations"] = [
            "Synthetic tiny corpus; measured durations are not accepted RPO/RTO or pilot capacity.",
            "Garage is a disposable S3-compatible test service, not a provider adoption or MinIO transferability certification.",
            "OIDC uses a test-only direct-grant client over isolated HTTP; browser/PKCE remains covered by existing OIDC CI, not this DR harness.",
            "Generated role passwords supplied separately; real secret escrow and recovery remain operator gated.",
            "No external destination or real secrets/records/pilot are accessed.",
        ]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", default="default")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    os.umask(0o077)
    report = {
        "schema": "oligospace-disaster-recovery-qualification/v1",
        "status": "failed",
        "source_commit": execute(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
        .decode()
        .strip(),
        "started_at": datetime.now(UTC).isoformat(),
        "native_architecture": platform.machine(),
        "stages": [],
        "negative_tests": [],
    }
    try:
        qualification(args.context, report)
        report["status"] = "passed"
    except Exception as error:
        # Only our fixed rule IDs are eligible for artifacts; never third-party text.
        text = str(error)
        report["failure_rule"] = (
            text
            if isinstance(error, QualificationError) and re.fullmatch(r"[a-z_]+", text)
            else "qualification_failed"
        )
        if isinstance(error, QualificationError) and error.diagnostic is not None:
            report["command_diagnostic"] = error.diagnostic
        raise SystemExit(
            "DEPLOY04 qualification failed; sanitized report retained"
        ) from None
    finally:
        report["finished_at"] = datetime.now(UTC).isoformat()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n")
    print("DEPLOY04 real restore qualification passed; sanitized report retained")


if __name__ == "__main__":
    main()
