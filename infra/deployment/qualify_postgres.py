"""Local disposable PostgreSQL/bootstrap qualification. No volume deletion.

Uses existing images (or CI-built images), no remote Docker endpoint, no host port.
Retains its unique test directory for evidence; removes only its own containers
and network. Never uses an existing project/database as an installation target.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import uuid

from evidence import credentials_absent_from_logs


def main() -> None:
    project = "oligospace-deploy01-test-" + uuid.uuid4().hex[:12]
    root = Path(__file__).resolve().parent
    directory = Path(tempfile.mkdtemp(prefix=project + "-"))
    data = directory / "postgres"
    data.mkdir()
    env = {
        "POSTGRES_PASSWORD": secrets.token_hex(24),
        **{
            key: secrets.token_hex(24)
            for key in (
                "MIGRATOR_PASSWORD",
                "APP_PASSWORD",
                "WORKER_PASSWORD",
                "IDENTITY_PASSWORD",
            )
        },
        "DEPLOY_TARGET": "disposable",
        "PILOT_PROJECT": project,
        "ENVIRONMENT": "production",
        "AUTH_MODE": "oidc",
        "OBJECT_STORAGE_ACCESS_KEY": secrets.token_hex(24),
        "OBJECT_STORAGE_SECRET_KEY": secrets.token_hex(24),
    }
    env["BOOTSTRAP_DATABASE_URL"] = (
        f"postgresql://postgres:{env['POSTGRES_PASSWORD']}@postgres/postgres"
    )
    env["DATABASE_URL"] = (
        f"postgresql+asyncpg://os_migrator:{env['MIGRATOR_PASSWORD']}@postgres/oligospace"
    )
    envfile = directory / "credentials.env"
    envfile.write_text("\n".join(f"{k}={v}" for k, v in env.items()))
    envfile.chmod(0o600)
    context = os.environ.get("DEPLOY_TEST_CONTEXT", "default")

    def run(*args: str, expected: int = 0) -> str:
        result = subprocess.run(
            ["docker", "--context", context, *args],
            env={**os.environ, **env},
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != expected:
            raise RuntimeError("qualification_command_failed (output suppressed)")
        return result.stdout.strip()

    # Refuse any TCP/SSH endpoint or inherited remote engine before mutations.
    endpoint = json.loads(run("context", "inspect", context))[0]["Endpoints"]["docker"][
        "Host"
    ]
    if not endpoint.startswith("unix://") or os.environ.get("DOCKER_HOST"):
        raise RuntimeError("local_unix_engine_required")
    pgimage = os.environ.get("DEPLOY_TEST_POSTGRES_IMAGE", "postgres:17.11-alpine")
    apiimage = os.environ.get("DEPLOY_TEST_API_IMAGE", "oligospace-api-tooling:latest")
    container = project + "-postgres"
    client = project + "-client"
    created_network = created_pg = False

    def sql(query: str) -> str:
        return run(
            "exec",
            "-u",
            "postgres",
            container,
            "psql",
            "-U",
            "postgres",
            "-d",
            "oligospace",
            "-At",
            "-v",
            "ON_ERROR_STOP=1",
            "-c",
            query,
        )

    def bootstrap(mode: str, expected: int = 0) -> str:
        return run(
            "run",
            "--rm",
            "--name",
            client,
            "--label",
            "org.oligospace.disposable=" + project,
            "--network",
            project,
            "--env-file",
            str(envfile),
            "--volume",
            f"{root}:/deployment:ro",
            apiimage,
            "micromamba",
            "run",
            "--name",
            "base",
            "python",
            "/deployment/bootstrap.py",
            mode,
            expected=expected,
        )

    evidence = {"project": project, "scope": "disposable_postgres_only", "checks": []}
    try:
        run(
            "network",
            "create",
            "--internal",
            "--label",
            "org.oligospace.disposable=" + project,
            project,
        )
        created_network = True
        run(
            "run",
            "--detach",
            "--name",
            container,
            "--label",
            "org.oligospace.disposable=" + project,
            "--network",
            project,
            "--network-alias",
            "postgres",
            "--env",
            "POSTGRES_PASSWORD",
            "--mount",
            f"type=bind,source={data},target=/var/lib/postgresql/data",
            pgimage,
        )
        created_pg = True
        for _ in range(60):
            result = subprocess.run(
                [
                    "docker",
                    "--context",
                    context,
                    "exec",
                    container,
                    "pg_isready",
                    "-U",
                    "postgres",
                ],
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                break
            time.sleep(1)
        else:
            raise RuntimeError("database_not_ready")
        bootstrap("initialize")
        # Simulate interruption after role/DB creation by restarting, then resume.
        run("restart", container)
        for _ in range(60):
            result = subprocess.run(
                [
                    "docker",
                    "--context",
                    context,
                    "exec",
                    container,
                    "pg_isready",
                    "-U",
                    "postgres",
                ],
                capture_output=True,
                check=False,
            )
            if result.returncode == 0:
                break
            time.sleep(1)
        bootstrap("initialize")
        assert bootstrap("migrate") == "migration_upgrade"
        assert sql("SELECT version_num FROM alembic_version") == "0004_scientific_jobs"
        sql(
            "SET ROLE os_migrator; CREATE TABLE deployment_marker(id integer PRIMARY KEY); INSERT INTO deployment_marker VALUES(1)"
        )
        assert bootstrap("migrate") == "migration_noop"
        assert sql("SELECT count(*) FROM deployment_marker") == "1"
        assert (
            sql(
                "SELECT rolsuper OR rolcreatedb OR rolcreaterole FROM pg_roles WHERE rolname='os_worker'"
            )
            == "f"
        )
        assert sql("SELECT has_table_privilege('os_worker','oligos','INSERT')") == "f"
        assert (
            sql(
                "SELECT has_table_privilege('os_worker','scientific_job_results','INSERT')"
            )
            == "t"
        )
        sql("ALTER ROLE os_worker CREATEDB")
        bootstrap("initialize", expected=1)
        sql("ALTER ROLE os_worker NOCREATEDB")  # only test-induced elevation
        sql("UPDATE alembic_version SET version_num='unrecognized_schema'")
        bootstrap("migrate", expected=1)
        assert sql("SELECT count(*) FROM deployment_marker") == "1"
        sql("UPDATE alembic_version SET version_num='0004_scientific_jobs'")
        assert bootstrap("migrate") == "migration_noop"
        evidence["checks"] = [
            "fresh_initialize",
            "restart_resume",
            "migration_head",
            "second_run_no_data_loss",
            "worker_privileges",
            "elevated_role_refused",
            "unknown_schema_refused",
            "resume_after_refusal",
        ]
        evidence["images"] = json.loads(
            run(
                "image", "inspect", pgimage, apiimage, "--format", "{{json .}}"
            ).splitlines()[0]
        ).get("Architecture")
        if not credentials_absent_from_logs(
            ["docker", "--context", context],
            container,
            [value for key, value in env.items() if "PASSWORD" in key],
        ):
            raise RuntimeError("credential_in_database_logs")
        evidence["checks"].append("no_generated_password_in_database_logs")
        (directory / "report.json").write_text(json.dumps(evidence, indent=2) + "\n")
        print(
            json.dumps(
                {"passed": evidence["checks"], "evidence_directory": str(directory)}
            )
        )
    finally:
        # Only our unique identifiers; no rm -v, down --volumes or prune.
        if created_pg:
            run("rm", "--force", container)
        if created_network:
            run("network", "rm", project)
        envfile.unlink(missing_ok=True)  # generated disposable credentials only


if __name__ == "__main__":
    main()
