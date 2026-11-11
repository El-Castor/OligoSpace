"""Disposable adaptation of the production pilot, never an activation command.

The legacy Chromium fixture supplies identities, not a runtime topology. Every
production service starts from compose.pilot.json; deviations are recorded before
any container starts. No registry upload, release gate override or real .env read.
"""

from __future__ import annotations

import copy
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
DEPLOY = ROOT / "infra/deployment"
CONTEXT = None
SEAWEED = "chrislusf/seaweedfs@sha256:57877e32bb90073b37dc109b438ba66e84fd5ed9ced5f5c04f56444ef243ce59"


def captured(command, data=None):
    if CONTEXT and command[0] == "docker" and "--context" not in command:
        command = ["docker", "--context", CONTEXT, *command[1:]]
    result = subprocess.run(
        command, input=data, capture_output=True, text=True, check=False
    )
    if result.returncode:
        # Docker diagnostics can contain substituted environment credentials.
        diagnostics = (result.stdout + result.stderr).lower()
        categories = [
            name
            for name, needle in {
                "docker_permission": "permission denied",
                "read_only": "read-only",
                "unhealthy": "unhealthy",
                "missing_file": "no such file",
                "network": "failed to fetch",
                "database": "sqlstate",
                "build": "failed to solve",
            }.items()
            if needle in diagnostics
        ]
        raise RuntimeError(
            "pilot_qualification_command_failed"
            + (":" + ",".join(categories) if categories else "")
        )
    return result.stdout.strip()


def interpolate(template, values):
    def substitute(match):
        key = match.group(1)
        if key not in values:
            raise ValueError("pilot_fixture_variable_missing")
        return json.dumps(str(values[key]))[1:-1]

    return json.loads(re.sub(r"\$\{([A-Z0-9_]+)(?::\?[^}]*)?\}", substitute, template))


def image_id(reference):
    value = captured(["docker", "image", "inspect", "--format", "{{.Id}}", reference])
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", value):
        raise ValueError("immutable_local_image_required")
    return value


def prepare(legacy, work, project, private_values, admin_password):
    if not project.startswith("oligospace-pilot-test-"):
        raise ValueError("disposable_project_required")
    global CONTEXT
    if os.environ.get("DOCKER_HOST") or os.environ.get("DOCKER_CONTEXT"):
        raise ValueError("local_docker_context_required")
    selected = captured(["docker", "context", "show"])
    context = json.loads(captured(["docker", "context", "inspect", selected]))
    if not context[0]["Endpoints"]["docker"]["Host"].startswith("unix://"):
        raise ValueError("local_docker_context_required")
    CONTEXT = selected
    # The private parent protects all fixture credentials. Docker mounts selected
    # child files directly, so it does not need world traversal of this directory.
    work.chmod(0o700)
    images = {}
    for role, service in (
        ("API", "api"),
        ("WEB", "web"),
        ("WORKER", "bioinfo-worker"),
        ("BROWSER", "browser"),
    ):
        build = legacy["services"].get(service, legacy["services"]["api"])["build"]
        if role == "WORKER" and service not in legacy["services"]:
            build = {"dockerfile": "infra/docker/bioinfo-worker.Dockerfile"}
        tag = project + "-" + role.lower()
        print("Building disposable pilot " + role.lower(), flush=True)
        captured(
            [
                "docker",
                "build",
                "--tag",
                tag,
                "--file",
                str(ROOT / build["dockerfile"]),
                str(ROOT),
            ]
        )
        images[role + "_IMAGE"] = image_id(tag)
    for role, reference in (
        ("POSTGRES", "postgres:17.11-alpine"),
        ("REDIS", "redis:7.4.10-alpine"),
        ("KEYCLOAK", "quay.io/keycloak/keycloak:26.7.2"),
        ("CADDY", "caddy:2.11.4-alpine"),
        ("MINIO", SEAWEED),
    ):
        captured(["docker", "pull", reference])
        images[role + "_IMAGE"] = image_id(reference)
    passwords = {
        key: secrets.token_urlsafe(36)
        for key in (
            "MIGRATOR_PASSWORD",
            "APP_PASSWORD",
            "WORKER_PASSWORD",
            "IDENTITY_PASSWORD",
            "REDIS_PASSWORD",
        )
    }
    private_values.update({key.lower(): value for key, value in passwords.items()})
    env = legacy["services"]["api"]["environment"]
    web = legacy["services"]["web"]["environment"]
    cert = work / "certs/ca.pem"
    key = work / "certs/key.pem"
    # Non-root Caddy reads the two-day synthetic key, protected by private parent.
    key.chmod(0o644)
    kc_config = work / "keycloak.conf"
    kc_config.write_text((DEPLOY / "keycloak.conf.example").read_text())
    kc_config.chmod(0o644)
    caddy = work / "Caddyfile"
    caddy.write_text((DEPLOY / "Caddyfile.template").read_text())
    caddy.chmod(0o644)
    values = dict(
        images,
        **passwords,
        OIDC_REALM="qualification",
        PILOT_PROJECT=project,
        PILOT_HOST="auth-qualification.test",
        APP_ORIGIN="https://auth-qualification.test",
        OIDC_ISSUER=env["OIDC_ISSUER"],
        OIDC_AUDIENCE="oligospace-api",
        OIDC_CLIENT_ID="oligospace-web",
        OIDC_CLIENT_SECRET=env["OIDC_CLIENT_SECRET"],
        NEXTAUTH_SECRET=web["NEXTAUTH_SECRET"],
        POSTGRES_BOOTSTRAP_PASSWORD=private_values["database_password"],
        KEYCLOAK_DB_USER="os_identity",
        KEYCLOAK_DB_PASSWORD=passwords["IDENTITY_PASSWORD"],
        S3_ACCESS_KEY=env["OBJECT_STORAGE_ACCESS_KEY"],
        S3_SECRET_KEY=env["OBJECT_STORAGE_SECRET_KEY"],
        S3_ADMIN_USER=env["OBJECT_STORAGE_ACCESS_KEY"],
        S3_ADMIN_PASSWORD=env["OBJECT_STORAGE_SECRET_KEY"],
        S3_BUCKET="pilot-synthetic",
        TLS_CONFIG=str(caddy),
        TLS_CERT=str(cert),
        TLS_KEY=str(key),
        TLS_CA=str(cert),
        PROXY_TRUSTED_CIDRS="172.18.0.0/16",
        KEYCLOAK_CONFIG=str(kc_config),
        INGRESS_IP="127.0.0.1",
        BUILD_ID=captured(["git", "-C", str(ROOT), "rev-parse", "HEAD"]),
        REDIS_URL="redis://:" + passwords["REDIS_PASSWORD"] + "@redis:6379/0",
    )
    for field, role, password in (
        ("APP_DATABASE_URL", "os_app", "APP_PASSWORD"),
        ("MIGRATION_DATABASE_URL", "os_migrator", "MIGRATOR_PASSWORD"),
        ("WORKER_DATABASE_URL", "os_worker", "WORKER_PASSWORD"),
    ):
        values[field] = (
            "postgresql+asyncpg://"
            + role
            + ":"
            + passwords[password]
            + "@postgres:5432/oligospace"
        )
    production = interpolate((DEPLOY / "compose.pilot.json").read_text(), values)
    sys.path.insert(0, str(DEPLOY))
    from policy import validate

    violations = validate(production, qualification=True)
    if violations:
        raise ValueError(
            "pilot_template_policy_refused:" + ",".join(sorted(set(violations)))
        )
    compose = copy.deepcopy(production)
    services = compose["services"]
    services["caddy"].pop("ports", None)
    services["keycloak"]["environment"].update(
        KC_BOOTSTRAP_ADMIN_USERNAME="synthetic-bootstrap",
        KC_BOOTSTRAP_ADMIN_PASSWORD=admin_password,
    )
    # Offline realm import is a separate disposable operation; the running server
    # retains the exact production `start` command and uses its PostgreSQL DB.
    services["keycloak"].setdefault("volumes", []).append(
        {
            "type": "bind",
            "source": str(work / "realm/qualification.json"),
            "target": "/fixtures/realm.json",
            "read_only": True,
        }
    )
    s3 = services["object-store"]
    s3.pop("healthcheck", None)  # Candidate readiness is checked by the S3 SDK.
    s3.update(
        command=[
            "mini",
            "-dir=/data",
            "-ip=" + project + "-object-store",
            "-ip.bind=0.0.0.0",
            "-s3.config=/etc/seaweedfs/s3.json",
        ],
        environment={},
        container_name=project + "-object-store",
    )
    config = work / "s3.json"
    config.write_text(
        json.dumps(
            {
                "identities": [
                    {
                        "name": "synthetic-pilot",
                        "credentials": [
                            {
                                "accessKey": values["S3_ACCESS_KEY"],
                                "secretKey": values["S3_SECRET_KEY"],
                            }
                        ],
                        "actions": ["Admin", "Read", "Write", "List", "Tagging"],
                    }
                ]
            }
        )
    )
    config.chmod(0o644)
    s3.setdefault("volumes", []).append(
        {
            "type": "bind",
            "source": str(config),
            "target": "/etc/seaweedfs/s3.json",
            "read_only": True,
        }
    )
    for name in ("api", "migrate"):
        services[name]["environment"]["OBJECT_STORAGE_ENDPOINT"] = "object-store:8333"
    browser = copy.deepcopy(legacy["services"]["browser"])
    browser.pop("build")
    browser.update(
        image=images["BROWSER_IMAGE"],
        networks=["ingress", "application"],
        profiles=["qualification"],
    )
    browser["environment"]["PILOT_STRICT_TLS"] = "1"
    # NSS trust setup applies to this test container only; no insecure Chromium flag.
    browser["entrypoint"] = [
        "/bin/sh",
        "-ec",
        'mkdir -p "$$HOME/.pki/nssdb"; certutil -N -d sql:"$$HOME/.pki/nssdb" --empty-password; certutil -A -d sql:"$$HOME/.pki/nssdb" -n pilot-synthetic-ca -t "C,," -i /certs/ca.pem; exec "$$@"',
        "pilot-browser",
    ]
    services["browser"] = browser
    bootstrap = copy.deepcopy(services["migrate"])
    bootstrap.update(
        profiles=["qualification"],
        command=[],
        entrypoint=["/opt/venv/bin/python", "/fixtures/bootstrap.py"],
    )
    bootstrap.setdefault("volumes", []).append(
        {
            "type": "bind",
            "source": str(DEPLOY / "bootstrap.py"),
            "target": "/fixtures/bootstrap.py",
            "read_only": True,
        }
    )
    bootstrap["environment"].update(
        passwords,
        DEPLOY_TARGET="disposable",
        PILOT_PROJECT=project,
        BOOTSTRAP_DATABASE_URL="postgresql://postgres:"
        + values["POSTGRES_BOOTSTRAP_PASSWORD"]
        + "@postgres:5432/postgres",
    )
    services["fixture-bootstrap"] = bootstrap
    (work / "pilot-values.json").write_text(json.dumps(values))
    (work / "pilot-qualified-template.json").write_text(json.dumps(production))
    (work / "pilot-deviations.json").write_text(
        json.dumps(
            {
                "scope": "disposable_only",
                "production_activation": "blocked",
                "deviations": [
                    "local immutable image config IDs; no registry approval",
                    "no host ingress publication",
                    "SeaweedFS 4.52 candidate; no provider adoption",
                    "offline synthetic realm import and bounded PostgreSQL fixture bootstrap",
                    "privileged fixture browser on application; untrusted probe separately ingress only",
                    "two-day synthetic CA trusted through NSS",
                    "candidate S3 readiness via SDK instead of MinIO health command",
                ],
            },
            indent=2,
        )
    )
    return compose


def narrow_proxy_trust(dc):
    # Compose chooses the disposable network. Inspect its actual subnet instead
    # of trusting every Docker/private address range or assigning static IPAM.
    captured(dc + ["create", "--pull", "never", "--no-build", "keycloak"])
    config = Path(dc[dc.index("--file") + 1])
    compose = json.loads(config.read_text())
    subnet = captured(
        [
            "docker",
            "network",
            "inspect",
            "--format",
            "{{(index .IPAM.Config 0).Subnet}}",
            compose["name"] + "_application",
        ]
    )
    network = ipaddress.ip_network(subnet)
    if not network.is_private or network.prefixlen < 16:
        raise ValueError("private_application_subnet_required")
    compose["services"]["keycloak"]["environment"]["KC_PROXY_TRUSTED_ADDRESSES"] = str(
        network
    )
    config.write_text(json.dumps(compose))


def bootstrap(dc):
    captured(dc + ["run", "--rm", "-T", "fixture-bootstrap", "initialize"])
    captured(dc + ["run", "--rm", "-T", "fixture-bootstrap", "migrate"])
    captured(dc + ["run", "--rm", "-T", "fixture-bootstrap", "migrate"])
    captured(
        dc
        + [
            "run",
            "--rm",
            "--no-deps",
            "-T",
            "keycloak",
            "--config-file=/etc/oligospace/keycloak.conf",
            "import",
            "--file=/fixtures/realm.json",
        ]
    )
    narrow_proxy_trust(dc)


def network_probe(dc, evidence):
    # No socket, host network, production credentials or application membership.
    endpoints = []
    for service, port in (
        ("postgres", 5432),
        ("redis", 6379),
        ("object-store", 8333),
        ("keycloak", 8080),
        ("api", 8000),
        ("web", 3000),
    ):
        container = captured(dc + ["ps", "--quiet", service])
        if not re.fullmatch(r"[0-9a-f]{12,64}", container):
            raise ValueError("probe_service_not_running")
        networks = json.loads(
            captured(
                [
                    "docker",
                    "inspect",
                    "--format",
                    "{{json .NetworkSettings.Networks}}",
                    container,
                ]
            )
        )
        addresses = [
            network["IPAddress"]
            for network in networks.values()
            if network.get("IPAddress")
        ]
        if not addresses:
            raise ValueError("probe_private_address_missing")
        endpoints.append((service, port))
        endpoints.extend((address, port) for address in addresses)
    script = (
        "import socket, ssl, urllib.request, json\nendpoints="
        + repr(endpoints)
        + "\n"
        + """
for host, port in endpoints:
 try:
  socket.create_connection((host,port),timeout=2).close()
 except OSError:
  continue
 raise SystemExit('private dependency reachable')
ctx=ssl.create_default_context(cafile='/certs/ca.pem')
import time
for attempt in range(120):
 try:
  urllib.request.urlopen('https://auth-qualification.test/realms/qualification/.well-known/openid-configuration',context=ctx,timeout=5)
  break
 except (OSError, urllib.error.URLError):
  time.sleep(2)
else:
 raise SystemExit('identity not ready')
for path in ['/admin/','/realms/master/.well-known/openid-configuration']:
 try:
  urllib.request.urlopen('https://auth-qualification.test'+path,context=ctx,timeout=10)
 except urllib.error.HTTPError as error:
  assert error.code in (403,404)
 else:
  raise SystemExit('identity administration exposed')
print('pilot_network_isolation_passed')
"""
    )
    config = Path(dc[dc.index("--file") + 1])
    compose = json.loads(config.read_text())
    probe = copy.deepcopy(compose["services"]["migrate"])
    probe.update(
        profiles=["qualification"],
        networks=["ingress"],
        environment={},
        depends_on={},
        entrypoint=["/opt/venv/bin/python"],
        command=[],
    )
    compose["services"]["untrusted-probe"] = probe
    probe_file = config.with_name("probe.json")
    probe_file.write_text(json.dumps(compose))
    probe_dc = dc.copy()
    probe_dc[probe_dc.index("--file") + 1] = str(probe_file)
    captured(
        probe_dc + ["run", "--rm", "--no-deps", "-T", "untrusted-probe", "-c", script]
    )
    (evidence / "pilot-network.json").write_text(
        json.dumps(
            {
                "ingress_only_probe": "passed",
                "private_dependencies": 6,
                "dns_and_direct_ip_endpoints": len(endpoints),
                "identity_admin_routes": 2,
                "fixture_browser": "privileged_application_network",
            }
        )
    )


def recovery_roundtrip(dc, work, evidence, log_checker):
    """Use DEPLOY04 Recovery unchanged against both pilot databases and S3.

    Only this disposable maintenance window adds a loopback S3 operator transport.
    It is removed before writers resume; production Compose has no such mapping.
    """
    import io
    from minio import Minio

    sys.path.insert(0, str(ROOT / "infra/backup"))
    from recovery import Recovery

    source_file = Path(dc[dc.index("--file") + 1])
    source = json.loads(source_file.read_text())
    project = source["name"]
    if not project.startswith("oligospace-pilot-test-"):
        raise ValueError("disposable_project_required")
    values = json.loads((work / "pilot-values.json").read_text())
    context = captured(["docker", "context", "show"])
    empty_env = work / "recovery.env"
    empty_env.write_text("")
    empty_env.chmod(0o600)
    running = captured(dc + ["ps", "--status", "running", "--services"]).split()
    data_services = {"postgres", "redis", "object-store"}
    writers = [name for name in running if name not in data_services]
    if writers:
        captured(dc + ["stop", *writers])
    target = copy.deepcopy(source)
    target["name"] = project + "-restore"
    target["services"]["object-store"]["container_name"] = (
        target["name"] + "-object-store"
    )
    target["services"]["object-store"]["command"] = [
        item.replace(project + "-object-store", target["name"] + "-object-store")
        for item in target["services"]["object-store"]["command"]
    ]
    target["services"]["fixture-bootstrap"]["environment"]["PILOT_PROJECT"] = target[
        "name"
    ]
    target_file = work / "restore-compose.json"
    target_dc = dc.copy()
    target_dc[target_dc.index("--file") + 1] = str(target_file)
    target_dc[target_dc.index("--project-name") + 1] = target["name"]

    def operator_transport(compose, path, command):
        compose["networks"]["operator"] = {}
        store = compose["services"]["object-store"]
        store["networks"] = ["data", "operator"]
        store["ports"] = [
            {
                "target": 8333,
                "published": "0",
                "host_ip": "127.0.0.1",
                "protocol": "tcp",
            }
        ]
        path.write_text(json.dumps(compose))
        captured(command + ["up", "--detach", "--no-deps", "object-store"])
        endpoint = captured(command + ["port", "object-store", "8333"])
        if not re.fullmatch(r"127\.0\.0\.1:[0-9]+", endpoint):
            raise ValueError("operator_loopback_required")
        client = Minio(
            endpoint,
            access_key=values["S3_ACCESS_KEY"],
            secret_key=values["S3_SECRET_KEY"],
            secure=False,
        )
        for attempt in range(60):
            try:
                client.list_buckets()
                return endpoint, client
            except Exception:
                time.sleep(1)
        raise ValueError("operator_s3_not_ready")

    def recovery_config(compose, path, endpoint, side):
        return dict(
            context=context,
            project=compose["name"],
            compose_file=str(path),
            env_file=str(empty_env),
            state_dir=str(work / ("recovery-state-" + side)),
            database_service="postgres",
            databases={
                "application": {"name": "oligospace", "user": "postgres"},
                "identity": {"name": "keycloak", "user": "postgres"},
            },
            writers=sorted(
                name
                for name, service in compose["services"].items()
                if name not in data_services and not service.get("profiles")
            ),
            non_writers=sorted(data_services),
            redis_service="redis",
            s3_service="object-store",
            external_writers_excluded=True,
            s3={
                "endpoint": endpoint,
                "secure": False,
                "access_key": values["S3_ACCESS_KEY"],
                "secret_key": values["S3_SECRET_KEY"],
            },
            buckets=[values["S3_BUCKET"]],
            source_revision=values["BUILD_ID"],
            configuration_files=[str(DEPLOY / "Caddyfile.template")],
            secret_inventory=[
                "APP_PASSWORD",
                "WORKER_PASSWORD",
                "IDENTITY_PASSWORD",
                "S3_SECRET_KEY",
            ],
        )

    try:
        endpoint, client = operator_transport(source, source_file, dc)
        if not client.bucket_exists(values["S3_BUCKET"]):
            client.make_bucket(values["S3_BUCKET"])
        payload = (
            b"Synthetic DEPLOY05 recovery sentinel; no scientific or personal data."
        )
        client.put_object(
            values["S3_BUCKET"],
            "qualification/sentinel.txt",
            io.BytesIO(payload),
            len(payload),
            content_type="text/plain",
            metadata={"qualification": "deploy05"},
        )
        key = work / "recovery.key"
        key.write_bytes(secrets.token_bytes(32))
        key.chmod(0o600)
        archive = work / "pilot-backup.osbackup"
        backup = Recovery(
            recovery_config(source, source_file, endpoint, "source")
        ).backup(archive, key)
        target_file.write_text(json.dumps(target))
        captured(target_dc + ["up", "--detach", "--wait", "postgres", "redis"])
        captured(target_dc + ["run", "--rm", "-T", "fixture-bootstrap", "initialize"])
        target_endpoint, target_client = operator_transport(
            target, target_file, target_dc
        )
        restore = Recovery(
            recovery_config(target, target_file, target_endpoint, "target")
        ).restore(archive, key)
        response = target_client.get_object(
            values["S3_BUCKET"], "qualification/sentinel.txt"
        )
        try:
            if response.read() != payload:
                raise ValueError("restored_sentinel_mismatch")
        finally:
            response.close()
            response.release_conn()
        # Recovery verifies all public-table hashes, ownership and ACLs in both
        # databases, plus object bytes/metadata. Confirm runtime can restart too.
        target["services"]["object-store"].pop("ports", None)
        target["services"]["object-store"]["networks"] = ["data"]
        target_file.write_text(json.dumps(target))
        narrow_proxy_trust(target_dc)
        captured(
            target_dc
            + [
                "up",
                "--detach",
                "--wait",
                "api",
                "web",
                "keycloak",
                "redis",
                "object-store",
                "bioinfo-worker",
                "scientific-scheduler",
                "caddy",
            ]
        )
        network_probe(target_dc, evidence)
        restored_logs = work / "restore-log-evidence"
        restored_logs.mkdir()
        if log_checker(target_dc, restored_logs) != "passed":
            raise ValueError("restored_runtime_log_gate_failed")
        (evidence / "pilot-restore-log-gate.json").write_text(
            (restored_logs / "secret-log-gate.json").read_text()
        )
        (evidence / "pilot-recovery.json").write_text(
            json.dumps(
                {
                    "backup": "passed",
                    "restore": "passed",
                    "integrity_verified": restore["integrity_verified"],
                    "target_runtime_restart": "passed",
                    "both_postgresql_databases": True,
                    "synthetic_s3_object": "passed",
                    "backup_seconds": backup["backup_seconds"],
                    "restore_seconds": restore["restore_seconds"],
                    "operator_transport": "disposable loopback only while all writers stopped",
                    "production_activation": "blocked",
                },
                indent=2,
            )
        )
    finally:
        # No volume deletion: uniquely labelled disposable volumes remain available
        # for explicit operator cleanup; neither production nor source data dropped.
        captured(target_dc + ["down", "--remove-orphans"])
        source["services"]["object-store"].pop("ports", None)
        source["services"]["object-store"]["networks"] = ["data"]
        source_file.write_text(json.dumps(source))
        captured(dc + ["up", "--detach", "--no-deps", "object-store"])
        if writers:
            captured(dc + ["start", *writers])


def main():
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scientific", action="store_true")
    args = parser.parse_args()
    command = [
        sys.executable,
        "-B",
        str(ROOT / "infra/auth-qualification/run.py"),
        "--pilot",
    ]
    if args.scientific:
        command.append("--scientific")
    return subprocess.run(command, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
