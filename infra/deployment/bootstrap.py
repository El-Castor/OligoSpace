"""Disposable-target bootstrap qualification, NOT a production installer.

No DROP, downgrade, seed, password rotation or real-host operation. Production
execution intentionally unavailable pending storage/security/restore approval.
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import sys

HEAD = "0004_scientific_jobs"


def role_is_bounded(row: dict) -> bool:
    return not any(
        row[key]
        for key in (
            "rolsuper",
            "rolcreatedb",
            "rolcreaterole",
            "rolreplication",
            "rolbypassrls",
            "member",
        )
    )


def migration_action(revisions: list[str]) -> str:
    if revisions == [HEAD]:
        return "noop"
    if not revisions:
        return "upgrade"
    # Updates need an explicitly reviewed source/target compatibility decision.
    raise ValueError("schema_incompatible")


def guard() -> None:
    if os.environ.get("DEPLOY_TARGET") != "disposable" or not os.environ.get(
        "PILOT_PROJECT", ""
    ).startswith("oligospace-deploy01-test-"):
        raise ValueError("disposable_target_required")


async def initialize() -> None:
    import asyncpg

    guard()
    connection = await asyncpg.connect(os.environ["BOOTSTRAP_DATABASE_URL"])
    try:
        # One session serializes resumable role/database creation; never drops data.
        await connection.execute("SELECT pg_advisory_lock(79103001)")
        for role, key in (
            ("os_migrator", "MIGRATOR_PASSWORD"),
            ("os_app", "APP_PASSWORD"),
            ("os_worker", "WORKER_PASSWORD"),
            ("os_identity", "IDENTITY_PASSWORD"),
        ):
            password = os.environ[key]
            if len(password) < 24:
                raise ValueError("credential_required")
            if not await connection.fetchval(
                "SELECT EXISTS(SELECT FROM pg_roles WHERE rolname=$1)", role
            ):
                literal = password.replace("'", "''")
                await connection.execute(
                    f"CREATE ROLE {role} LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD '{literal}'"
                )
            row = await connection.fetchrow(
                "SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls, EXISTS(SELECT FROM pg_auth_members WHERE member=pg_roles.oid) AS member FROM pg_roles WHERE rolname=$1",
                role,
            )
            if not role_is_bounded(row):
                raise ValueError("existing_role_not_bounded")
        for database, owner in (
            ("oligospace", "os_migrator"),
            ("keycloak", "os_identity"),
        ):
            row = await connection.fetchrow(
                "SELECT pg_get_userbyid(datdba) AS owner FROM pg_database WHERE datname=$1",
                database,
            )
            if row and row["owner"] != owner:
                raise ValueError("database_owner_mismatch")
            if not row:
                await connection.execute(f"CREATE DATABASE {database} OWNER {owner}")
            await connection.execute(f"REVOKE ALL ON DATABASE {database} FROM PUBLIC")
        await connection.execute(
            "GRANT CONNECT ON DATABASE oligospace TO os_app, os_worker"
        )
    finally:
        await connection.close()


async def migrate() -> str:
    import asyncpg

    guard()
    url = os.environ["DATABASE_URL"].replace(
        "postgresql+asyncpg://", "postgresql://", 1
    )
    connection = await asyncpg.connect(url)
    try:
        await connection.execute("SELECT pg_advisory_lock(79103002)")
        exists = await connection.fetchval(
            "SELECT to_regclass('public.alembic_version')"
        )
        revisions = (
            [
                r["version_num"]
                for r in await connection.fetch(
                    "SELECT version_num FROM alembic_version"
                )
            ]
            if exists
            else []
        )
        if not revisions:
            count = await connection.fetchval(
                "SELECT count(*) FROM information_schema.tables WHERE table_schema='public'"
            )
            if count:
                raise ValueError("unversioned_database_not_empty")
        action = migration_action(revisions)
        if action == "upgrade":
            # No shell and no DB URL in argv/output. Retain lock on this session.
            result = await asyncio.to_thread(
                subprocess.run,
                ["micromamba", "run", "--name", "base", "alembic", "upgrade", "head"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if result.returncode:
                raise ValueError("migration_failed")
        final = [
            r["version_num"]
            for r in await connection.fetch("SELECT version_num FROM alembic_version")
        ]
        if final != [HEAD]:
            raise ValueError("schema_incompatible")
        # Idempotent post-migration privileges; API CRUD, worker bounded job/audit DML.
        await connection.execute("REVOKE CREATE ON SCHEMA public FROM PUBLIC")
        await connection.execute("GRANT USAGE ON SCHEMA public TO os_app, os_worker")
        await connection.execute(
            "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO os_app"
        )
        await connection.execute(
            "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO os_app"
        )
        await connection.execute(
            "GRANT SELECT, INSERT, UPDATE ON scientific_jobs, scientific_job_attempts, scientific_job_results TO os_worker"
        )
        await connection.execute("GRANT INSERT ON audit_events TO os_worker")
        return action
    finally:
        await connection.close()


def main() -> int:
    try:
        guard()
        mode = sys.argv[1] if len(sys.argv) == 2 else ""
        if mode == "initialize":
            asyncio.run(initialize())
            print("bootstrap_initialized")
        elif mode == "migrate":
            print("migration_" + asyncio.run(migrate()))
        else:
            raise ValueError("unknown_operation")
        return 0
    except Exception:
        # Exceptions may contain DSNs or SQL; never include them in diagnostics.
        print("bootstrap_refused_or_failed", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
