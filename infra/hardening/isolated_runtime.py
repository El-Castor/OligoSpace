"""Qualify supplied local candidate images using disposable PG/Redis only.

No published ports, host service connections, real migrations or scientific
result claims. Full OIDC/RLS/scientific integration remains a separate gate.
"""

import argparse
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import uuid


def compose_spec(api, worker, postgres, redis, credentials):
    common = {
        "read_only": True,
        "cap_drop": ["ALL"],
        "security_opt": ["no-new-privileges:true"],
        "pids_limit": 128,
        "mem_limit": "512m",
        "cpus": 1.0,
        "restart": "no",
        "networks": ["isolated"],
        "pull_policy": "never",
        "tmpfs": ["/tmp:rw,nosuid,nodev,noexec,size=64m,mode=1777"],
    }
    application = {
        **common,
        "user": "1000:1000",
        "env_file": [str(credentials)],
        # Credentials are injected by Docker from a private 0600 file, never
        # interpolated in Compose JSON or commands. Reference mount is read-only.
        "volumes": [f"{credentials}:/run/secrets/runtime.env:ro"],
    }
    return {
        "networks": {"isolated": {"internal": True}},
        "services": {
            "postgres": {
                **common,
                "image": postgres,
                "user": "70:70",
                "env_file": [str(credentials.parent / "postgres.env")],
                "environment": {
                    "POSTGRES_DB": "qualification",
                    "POSTGRES_USER": "qualification",
                    "PGDATA": "/var/lib/postgresql/data/pgdata",
                },
                "tmpfs": common["tmpfs"]
                + [
                    "/var/lib/postgresql/data:rw,nosuid,nodev,noexec,size=256m,uid=70,gid=70,mode=0700",
                    "/var/run/postgresql:rw,nosuid,nodev,noexec,size=4m,uid=70,gid=70,mode=0700",
                ],
                "healthcheck": {
                    "test": [
                        "CMD",
                        "pg_isready",
                        "-U",
                        "qualification",
                        "-d",
                        "qualification",
                    ],
                    "interval": "2s",
                    "timeout": "2s",
                    "retries": 40,
                },
            },
            "redis": {
                **common,
                "image": redis,
                "user": "999:999",
                "entrypoint": ["redis-server"],
                "command": ["/run/secrets/redis.conf"],
                "tmpfs": common["tmpfs"]
                + ["/data:rw,nosuid,nodev,noexec,size=64m,uid=999,gid=999,mode=0700"],
                "volumes": [
                    f"{credentials.parent / 'redis.conf'}:/run/secrets/redis.conf:ro"
                ],
            },
            "api": {
                **application,
                "image": api,
                "depends_on": {
                    "postgres": {"condition": "service_healthy"},
                    "redis": {"condition": "service_started"},
                },
            },
            "worker": {
                **application,
                "image": worker,
                "depends_on": {
                    "postgres": {"condition": "service_healthy"},
                    "redis": {"condition": "service_started"},
                },
            },
        },
    }


def runtime_safe(info, network):
    host = info.get("HostConfig", {})
    return bool(
        info.get("State", {}).get("Running")
        and info.get("Config", {}).get("User", "").split(":")[0]
        not in ("", "0", "root")
        and host.get("ReadonlyRootfs")
        and not host.get("Privileged")
        and "ALL" in host.get("CapDrop", [])
        and not host.get("CapAdd")
        and not host.get("Devices")
        and host.get("PidMode") != "host"
        and host.get("IpcMode") != "host"
        and any(
            s in host.get("SecurityOpt", [])
            for s in ("no-new-privileges", "no-new-privileges:true")
        )
        and 0 < host.get("PidsLimit", 0) <= 128
        and 0 < host.get("Memory", 0) <= 512 * 1024 * 1024
        and 0 < host.get("NanoCpus", 0) <= 1000000000
        and not host.get("PortBindings")
        and host.get("Tmpfs")
        and all("size=" in v for v in host["Tmpfs"].values())
        and set(info.get("NetworkSettings", {}).get("Networks", {})) == {network}
        and all(
            (
                not m.get("RW")
                or (m.get("Type") == "tmpfs" and m.get("Destination") in host["Tmpfs"])
            )
            and "docker.sock" not in m.get("Source", "")
            for m in info.get("Mounts", [])
        )
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "context",
        "api-image",
        "worker-image",
        "postgres-image",
        "redis-image",
    ):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--api-python", default="/opt/venv/bin/python")
    parser.add_argument("--worker-python", default="/opt/venv/bin/python")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    docker = ["docker", "--context", args.context]

    def run(command, *, check=True, timeout=120):
        result = subprocess.run(
            command, text=True, capture_output=True, timeout=timeout, check=False
        )
        if check and result.returncode:
            raise RuntimeError("ISOLATED_COMMAND_FAILED")
        return result

    endpoint = json.loads(run(docker + ["context", "inspect", args.context]).stdout)[0][
        "Endpoints"
    ]["docker"]["Host"]
    if not endpoint.startswith("unix://") or os.environ.get("DOCKER_HOST"):
        parser.error("explicit local Unix engine required")
    project = "oligospace-hardening-" + uuid.uuid4().hex[:12]
    report = {
        "schema": "isolated-runtime/v1",
        "project": project,
        "execution": "not_executed",
        "checks": {},
        "scientific_jobs": "not_verified",
        "schema_migrations": "not_verified",
        "oidc_rls": "not_verified",
        "publication_authorized": False,
    }
    with tempfile.TemporaryDirectory(prefix=project + "-") as directory:
        root = Path(directory)
        password, redis_password = secrets.token_hex(24), secrets.token_hex(24)
        credentials = root / "runtime.env"
        credentials.write_text(
            f"ENVIRONMENT=test\nAUTH_MODE=development\nDATABASE_URL=postgresql+asyncpg://qualification:{password}@postgres/qualification\nREDIS_URL=redis://:{redis_password}@redis:6379/0\n"
        )
        credentials.chmod(0o600)
        pg_env = root / "postgres.env"
        pg_env.write_text("POSTGRES_PASSWORD=" + password + "\n")
        pg_env.chmod(0o600)
        # Redis reads its config as uid999; only that generated file is readable.
        redis_config = root / "redis.conf"
        redis_config.write_text(
            f'bind 0.0.0.0\nprotected-mode yes\nrequirepass {redis_password}\nsave ""\nappendonly no\n'
        )
        redis_config.chmod(0o444)
        spec = compose_spec(
            args.api_image,
            args.worker_image,
            args.postgres_image,
            args.redis_image,
            credentials,
        )
        compose_file = root / "compose.json"
        compose_file.write_text(json.dumps(spec))
        dc = docker + [
            "compose",
            "--project-name",
            project,
            "--file",
            str(compose_file),
        ]
        containers = {}
        try:
            # Resolve all images locally first; Compose is forbidden to pull.
            report["images"] = {}
            for role, image in (
                ("api", args.api_image),
                ("worker", args.worker_image),
                ("postgres", args.postgres_image),
                ("redis", args.redis_image),
            ):
                info = json.loads(run(docker + ["image", "inspect", image]).stdout)[0]
                report["images"][role] = {
                    "id": info["Id"],
                    "architecture": info["Architecture"],
                }
            run(dc + ["up", "--detach", "--wait", "--wait-timeout", "100"], timeout=150)
            network = project + "_isolated"
            network_info = json.loads(
                run(docker + ["network", "inspect", network]).stdout
            )[0]
            report["checks"]["network_internal"] = network_info.get("Internal") is True
            for role in spec["services"]:
                container = run(dc + ["ps", "--quiet", role]).stdout.strip()
                containers[role] = container
                info = json.loads(run(docker + ["inspect", container]).stdout)[0]
                report["checks"][role + "_runtime_controls"] = runtime_safe(
                    info, network
                )
            live = "import json,urllib.request; assert json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/live',timeout=3))['status']=='ok'; assert json.load(urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health/ready',timeout=3))['status']=='ready'"
            ping = "from oligospace_bioinfo.celery_app import app; assert app.control.ping(timeout=3)"
            for role, python, code in (
                ("api", args.api_python, live),
                ("worker", args.worker_python, ping),
            ):
                for attempt in range(30):
                    if (
                        run(
                            docker + ["exec", containers[role], python, "-c", code],
                            check=False,
                            timeout=10,
                        ).returncode
                        == 0
                    ):
                        report["checks"][role + "_ready"] = True
                        break
                    time.sleep(1)
                else:
                    report["checks"][role + "_ready"] = False
            for role, container in containers.items():
                logs = run(docker + ["logs", container], check=False)
                report["checks"][role + "_credentials_absent_from_logs"] = not any(
                    s in logs.stdout + logs.stderr for s in (password, redis_password)
                )
            run(dc + ["stop", "--timeout", "20"])
            for role, container in containers.items():
                state = json.loads(run(docker + ["inspect", container]).stdout)[0][
                    "State"
                ]
                report["checks"][role + "_graceful_stop"] = (
                    not state["Running"]
                    and not state.get("OOMKilled")
                    and state["ExitCode"] in (0, 143)
                )
            report["execution"] = (
                "passed" if all(report["checks"].values()) else "failed"
            )
        except (
            RuntimeError,
            subprocess.SubprocessError,
            ValueError,
            KeyError,
            OSError,
        ):
            report["execution"] = "failed"
            report["rule_id"] = "ISOLATED_RUNTIME_FAILED"
        finally:
            try:
                cleanup = run(
                    dc + ["down", "--timeout", "10", "--remove-orphans"], check=False
                )
                report["cleanup"] = "passed" if cleanup.returncode == 0 else "failed"
            except (OSError, subprocess.SubprocessError):
                report["cleanup"] = "failed"
            if report["cleanup"] != "passed":
                report["execution"] = "failed"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(0 if report["execution"] == "passed" else 1)


if __name__ == "__main__":
    main()
