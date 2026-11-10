"""Explicit local Compose recovery operations. Never deploys or deletes volumes."""

import argparse
from contextlib import contextmanager
from datetime import datetime, UTC
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

from minio import Minio
from archive import (
    protected,
    seal,
    unseal,
    manifest_files,
    digest,
    key_bytes,
    fsync_directory,
)
from s3 import export_buckets, restore_buckets, validate_export, require_empty

IDENTIFIER = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]{0,62}\Z")


class Recovery:
    def __init__(self, config: dict):
        self.config = config
        self.state = Path(config["state_dir"])
        self.dc = [
            "docker",
            "--context",
            config["context"],
            "compose",
            "--project-name",
            config["project"],
            "--file",
            str(config["compose_file"]),
            "--env-file",
            str(config["env_file"]),
        ]
        s3 = config["s3"]
        if not s3.get("access_key") or not s3.get("secret_key"):
            raise ValueError("secrets_missing")
        if not s3.get("secure", True) and s3["endpoint"].split(":")[0] not in (
            "127.0.0.1",
            "localhost",
            "[::1]",
        ):
            raise ValueError("s3_tls_or_local_tunnel_required")
        self.client = Minio(
            s3["endpoint"],
            access_key=s3["access_key"],
            secret_key=s3["secret_key"],
            secure=s3.get("secure", True),
        )

    def _call(self, args, *, data=None, output=None, source=None):
        result = subprocess.run(
            args,
            input=data,
            stdin=source,
            stdout=output or subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=1800,
        )
        if result.returncode:
            raise ValueError("operation_failed_output_withheld")
        return result.stdout if output is None else b""

    def _compose(self, *args, **kwargs):
        return self._call(self.dc + list(args), **kwargs)

    @contextmanager
    def _lock(self):
        if self.state.is_symlink() or not self.state.is_absolute():
            raise ValueError("private_absolute_state_required")
        self.state.mkdir(mode=0o700, parents=True, exist_ok=True)
        if self.state.stat().st_mode & 0o077 or self.state.stat().st_uid != os.getuid():
            raise ValueError("private_state_required")
        lock = self.state / "operation.lock"
        if lock.is_symlink():
            raise ValueError("unsafe_lock")
        with lock.open("a") as handle:
            lock.chmod(0o600)
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ValueError("operation_already_running") from error
            yield

    def _preflight(self):
        c = self.config
        if os.environ.get("DOCKER_HOST") or os.environ.get("DOCKER_CONTEXT"):
            raise ValueError("explicit_local_context_required")
        context = json.loads(
            self._call(
                [
                    "docker",
                    "--context",
                    c["context"],
                    "context",
                    "inspect",
                    c["context"],
                ]
            )
        )
        if not context[0]["Endpoints"]["docker"]["Host"].startswith("unix://"):
            raise ValueError("local_context_required")
        for name in ("compose_file", "env_file"):
            path = Path(c[name])
            if not path.is_absolute():
                raise ValueError("absolute_config_paths_required")
            if name == "env_file":
                protected(path)
            elif not path.is_file() or path.is_symlink():
                raise ValueError("compose_file_required")
        if c.get("external_writers_excluded") is not True:
            raise ValueError("exclusive_maintenance_window_required")
        if set(c["databases"]) != {"application", "identity"} or not re.fullmatch(
            r"[0-9a-f]{40}", c["source_revision"]
        ):
            raise ValueError("source_and_databases_required")
        for database in c["databases"].values():
            if not all(IDENTIFIER.fullmatch(database[k]) for k in ("name", "user")):
                raise ValueError("invalid_database_identifier")
        if c["databases"]["application"]["name"] == c["databases"]["identity"]["name"]:
            raise ValueError("separate_databases_required")
        resolved = json.loads(self._compose("config", "--format", "json"))
        services = set(resolved["services"])
        # Explicitly account for every service; an omitted writer cannot be assumed safe.
        readers = set(c.get("non_writers", [c["database_service"], "redis", "s3"]))
        if (
            set(c["writers"]) & readers
            or set(c["writers"]) | readers != services
            or c["database_service"] not in readers
        ):
            raise ValueError("complete_writer_inventory_required")
        safe_nonwriters = {
            c["database_service"],
            c.get("redis_service", "redis"),
            c.get("s3_service", "s3"),
        }
        if not readers <= safe_nonwriters or readers & {
            "api",
            "keycloak",
            "bioinfo-worker",
            "scientific-scheduler",
            "web",
            "proxy",
            "caddy",
        }:
            raise ValueError("invalid_nonwriter_classification")
        self.resolved = resolved
        if not c["buckets"] or len(c["buckets"]) != len(set(c["buckets"])):
            raise ValueError("bucket_inventory_required")
        if {b.name for b in self.client.list_buckets()} - set(c["buckets"]):
            raise ValueError("unlisted_visible_bucket")
        for name in c.get("secret_inventory", []):
            if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
                raise ValueError("secret_names_only")

    def _running(self):
        return [
            name
            for name in self._compose("ps", "--status", "running", "--services")
            .decode()
            .split()
            if name in self.config["writers"]
        ]

    def _stop(self, names):
        if names:
            self._compose("stop", "--timeout", "120", *names)

    def _assert_stopped(self):
        if self._running():
            raise ValueError("writers_still_running")

    def _resume(self, names):
        if not names:
            return
        self._compose("start", *names)
        deadline = time.monotonic() + 180
        while time.monotonic() < deadline:
            ids = self._compose("ps", "--all", "--quiet", *names).decode().split()
            if ids:
                inspect = json.loads(
                    self._call(
                        ["docker", "--context", self.config["context"], "inspect", *ids]
                    )
                )
                if len(inspect) == len(names) and all(
                    item["State"]["Running"]
                    and item["State"].get("Health", {}).get("Status", "healthy")
                    == "healthy"
                    for item in inspect
                ):
                    return
            time.sleep(2)
        raise ValueError("source_resume_not_healthy")

    def _pg(self, role, executable, *args, **kwargs):
        db = self.config["databases"][role]
        return self._compose(
            "exec",
            "-T",
            self.config["database_service"],
            executable,
            "--username",
            db["user"],
            "--dbname",
            db["name"],
            *args,
            **kwargs,
        )

    def _sql(self, role, sql):
        return (
            self._pg(role, "psql", "-X", "-A", "-t", "-v", "ON_ERROR_STOP=1", "-c", sql)
            .decode()
            .strip()
        )

    def _assert_no_sessions(self):
        # Each query runs in one DB, counting every OTHER session in both databases.
        names = ",".join(
            "'" + d["name"] + "'" for d in self.config["databases"].values()
        )
        count = self._sql(
            "application",
            f"SELECT count(*) FROM pg_stat_activity WHERE datname IN ({names}) AND pid <> pg_backend_pid() AND backend_type = 'client backend'",
        )
        if count != "0":
            raise ValueError("database_clients_still_connected")

    def _inventory(self, role):
        schemas = self._sql(
            role,
            "SELECT count(*) FROM information_schema.tables WHERE table_schema NOT IN ('public','information_schema') AND table_schema NOT LIKE 'pg_%'",
        )
        if schemas != "0":
            raise ValueError("nonpublic_schema_requires_extended_contract")
        tables = self._sql(
            role,
            "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename",
        ).splitlines()
        result = {}
        for table in tables:
            if not IDENTIFIER.fullmatch(table):
                raise ValueError("unexpected_table_identifier")
            # SHA256 over the exact sorted JSON rows, not counts alone.
            with tempfile.TemporaryFile() as rows:
                self._pg(
                    role,
                    "psql",
                    "-X",
                    "-A",
                    "-t",
                    "-v",
                    "ON_ERROR_STOP=1",
                    "-c",
                    f'SELECT row_to_json(t)::text FROM public."{table}" t ORDER BY row_to_json(t)::text',
                    output=rows,
                )
                rows.seek(0)
                sha = hashlib.sha256()
                count = 0
                for line in rows:
                    sha.update(line)
                    count += 1
                result[table] = {"rows": count, "sha256": sha.hexdigest()}
        return result

    def _attachment_integrity(self, buckets):
        if (
            self._sql(
                "application", "SELECT to_regclass('public.attachments') IS NOT NULL"
            )
            != "t"
        ):
            return
        bucket = self.config.get("attachment_bucket")
        if bucket is None and len(self.config["buckets"]) == 1:
            bucket = self.config["buckets"][0]
        objects = {
            obj["key"]: obj
            for b in buckets
            if b["bucket"] == bucket
            for obj in b["objects"]
        }
        records = json.loads(
            self._sql(
                "application",
                "SELECT coalesce(json_agg(a), '[]'::json) FROM (SELECT object_key, sha256, size_bytes, content_type FROM attachments) a",
            )
        )
        for record in records:
            obj = objects.get(record["object_key"])
            if (
                obj is None
                or obj["sha256"] != record["sha256"]
                or obj["size"] != record["size_bytes"]
                or obj["content_type"] != record["content_type"]
            ):
                raise ValueError("attachment_object_integrity_failed")

    def _roles(self):
        # Password verifiers are deliberately excluded; restore secrets separately.
        return json.loads(
            self._sql(
                "application",
                "SELECT coalesce(json_agg(r ORDER BY r.rolname), '[]'::json) FROM (SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin, rolreplication, rolbypassrls, rolconnlimit, rolvaliduntil, rolconfig FROM pg_roles WHERE rolname NOT LIKE 'pg_%') r",
            )
        )

    def _memberships(self):
        return json.loads(
            self._sql(
                "application",
                "SELECT coalesce(json_agg(r ORDER BY r.role, r.member), '[]'::json) FROM (SELECT a.rolname AS role, b.rolname AS member, m.admin_option, m.inherit_option, m.set_option FROM pg_auth_members m JOIN pg_roles a ON a.oid=m.roleid JOIN pg_roles b ON b.oid=m.member WHERE b.rolname NOT LIKE 'pg_%') r",
            )
        )

    def _empty_databases(self):
        for role in self.config["databases"]:
            # public itself exists in a new PostgreSQL database; user functions,
            # custom types, extensions and other schemas also make it nonempty.
            objects = self._sql(
                role,
                "SELECT (SELECT count(*) FROM pg_namespace WHERE nspname NOT IN ('public','information_schema') AND nspname NOT LIKE 'pg_%') + (SELECT count(*) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE n.nspname='public') + (SELECT count(*) FROM pg_type t JOIN pg_namespace n ON n.oid=t.typnamespace WHERE n.nspname='public') + (SELECT count(*) FROM pg_extension WHERE extname <> 'plpgsql')",
            )
            if objects != "0":
                raise ValueError("nonempty_database_target")
            if (
                self._sql(
                    role,
                    "SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace WHERE n.nspname NOT LIKE 'pg_%' AND n.nspname <> 'information_schema' AND c.relkind IN ('r','p','v','m','S','f')",
                )
                != "0"
            ):
                raise ValueError("nonempty_database_target")

    def _restore_database(self, role, dump):
        with dump.open("rb") as source:
            # stdin is streamed without putting a dump/password in argv or logs.
            result = subprocess.run(
                self.dc
                + [
                    "exec",
                    "-T",
                    self.config["database_service"],
                    "pg_restore",
                    "--username",
                    self.config["databases"][role]["user"],
                    "--dbname",
                    self.config["databases"][role]["name"],
                    "--exit-on-error",
                    "--single-transaction",
                ],
                stdin=source,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                timeout=1800,
                check=False,
            )
        if result.returncode:
            raise ValueError("database_restore_failed")

    def backup(self, destination: Path, key_file: Path) -> dict:
        start = time.monotonic()
        with self._lock():
            self._preflight()
            running = self._running()
            try:
                self._stop(running)
                self._assert_stopped()
                self._assert_no_sessions()
                key_bytes(key_file)
                with tempfile.TemporaryDirectory(
                    prefix="oligospace-recovery-"
                ) as directory:
                    root = Path(directory)
                    manifest = {
                        "schema": "oligospace-recovery/v1",
                        "created_utc": datetime.now(UTC).isoformat(),
                        "source_revision": self.config["source_revision"],
                        "source_project": self.config["project"],
                        "consistency": "all_declared_writers_stopped_external_writers_excluded",
                        "databases": {},
                        "roles": self._roles(),
                        "memberships": self._memberships(),
                        "configuration": [],
                        "secret_inventory": self.config.get("secret_inventory", []),
                    }
                    for role, database in self.config["databases"].items():
                        inventory = self._inventory(role)
                        filename = role + ".dump"
                        with (root / filename).open("xb") as out:
                            self._pg(
                                role,
                                "pg_dump",
                                "--format=custom",
                                "--compress=6",
                                output=out,
                            )
                        with (root / filename).open("rb") as inp:
                            listing = self._compose(
                                "exec",
                                "-T",
                                self.config["database_service"],
                                "pg_restore",
                                "--list",
                                source=inp,
                            )
                        (root / (role + ".toc")).write_bytes(listing)
                        manifest["databases"][role] = {
                            "name": database["name"],
                            "file": filename,
                            "server_version": self._sql(
                                role, "SHOW server_version_num"
                            ),
                            "tables": inventory,
                        }
                    manifest["buckets"] = export_buckets(
                        self.client, self.config["buckets"], root
                    )
                    self._attachment_integrity(manifest["buckets"])
                    for i, filename in enumerate(
                        self.config.get("configuration_files", [])
                    ):
                        path = Path(filename)
                        if path.is_symlink() or not path.is_file():
                            raise ValueError("configuration_missing")
                        # Explicit non-secret allow-list; contents are still encrypted.
                        dest = root / "configuration" / f"{i}.bin"
                        dest.parent.mkdir(mode=0o700, exist_ok=True)
                        shutil.copyfile(path, dest)
                        manifest["configuration"].append(
                            {
                                "name": path.name,
                                "file": dest.relative_to(root).as_posix(),
                            }
                        )
                    self._assert_stopped()
                    self._assert_no_sessions()
                    for role in self.config["databases"]:
                        if (
                            self._inventory(role)
                            != manifest["databases"][role]["tables"]
                        ):
                            raise ValueError("database_changed_during_capture")
                    manifest["files"] = manifest_files(root)
                    (root / "manifest.json").write_text(
                        json.dumps(manifest, sort_keys=True)
                    )
                    seal(root, destination, key_file)
            finally:
                self._resume(running)
        return {
            "backup_seconds": round(time.monotonic() - start, 3),
            "archive_sha256": digest(destination),
            "archive_bytes": destination.stat().st_size,
            "source_resumed": True,
        }

    def restore(self, archive: Path, key_file: Path) -> dict:
        start = time.monotonic()
        with self._lock():
            self._preflight()
            self._assert_stopped()
            marker = self.state / "restore-in-progress.json"
            if marker.exists():
                raise ValueError("interrupted_target_requires_new_empty_target")
            self._assert_no_sessions()
            with tempfile.TemporaryDirectory(
                prefix="oligospace-recovery-"
            ) as directory:
                root = Path(directory) / "verified"
                manifest = unseal(archive, root, key_file)
                if set(manifest.get("databases", {})) != {
                    "application",
                    "identity",
                } or {b["bucket"] for b in manifest.get("buckets", [])} != set(
                    self.config["buckets"]
                ):
                    raise ValueError("incomplete_backup")
                for role, entry in manifest["databases"].items():
                    if (
                        entry["file"] != role + ".dump"
                        or entry["file"] not in manifest["files"]
                        or role + ".toc" not in manifest["files"]
                        or not entry["tables"]
                    ):
                        raise ValueError("missing_database_backup")
                    target_version = self._sql(role, "SHOW server_version_num")
                    if (
                        int(target_version) // 10000
                        != int(entry["server_version"]) // 10000
                    ):
                        raise ValueError("database_major_version_mismatch")
                validate_export(manifest["buckets"], root)
                if (
                    manifest.get("roles") != self._roles()
                    or manifest.get("memberships") != self._memberships()
                ):
                    raise ValueError("preprovisioned_roles_and_memberships_must_match")
                self._empty_databases()
                require_empty(self.client, manifest["buckets"])
                marker.write_text(
                    json.dumps(
                        {"status": "restoring", "archive_sha256": digest(archive)}
                    )
                )
                marker.chmod(0o600)
                with marker.open("rb") as journal:
                    os.fsync(journal.fileno())
                fsync_directory(self.state)
                # Failure leaves this marker AND writers stopped; never auto-clears.
                for role, entry in manifest["databases"].items():
                    self._restore_database(role, root / entry["file"])
                    if self._inventory(role) != entry["tables"]:
                        raise ValueError("restored_database_fidelity_failed")
                self._attachment_integrity(manifest["buckets"])
                restore_buckets(self.client, manifest["buckets"], root)
                verified = self.state / "restore-verified.json"
                marker.rename(verified)
                verified.write_text(
                    json.dumps(
                        {
                            "status": "integrity_verified_services_stopped",
                            "archive_sha256": digest(archive),
                            "restore_seconds": round(time.monotonic() - start, 3),
                        }
                    )
                )
                verified.chmod(0o600)
                with verified.open("rb") as journal:
                    os.fsync(journal.fileno())
                fsync_directory(self.state)
                return {
                    "restore_seconds": round(time.monotonic() - start, 3),
                    "integrity_verified": True,
                    "services_started": False,
                }


def main():
    parser = argparse.ArgumentParser(
        description="Coordinated local backup/restore; no deployment or volume deletion"
    )
    parser.add_argument("action", choices=["backup", "restore"])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--key-file", type=Path, required=True)
    parser.add_argument("--archive", type=Path, required=True)
    args = parser.parse_args()
    try:
        protected(args.config)
        recovery = Recovery(json.loads(args.config.read_text()))
        result = getattr(recovery, args.action)(args.archive, args.key_file)
        print(json.dumps({"status": "passed", **result}))
        return 0
    except Exception:
        print(
            json.dumps(
                {"status": "failed", "rule": "recovery_refused_details_withheld"}
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
