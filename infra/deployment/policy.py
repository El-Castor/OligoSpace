"""Read resolved Compose JSON on stdin. Never print configuration or secrets.

Static acceptance is deliberately distinct from release/runtime qualification.
Only this independently defined deployment topology is supported.
"""

from __future__ import annotations

import ipaddress
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse

SERVICES = {
    "postgres",
    "redis",
    "object-store",
    "keycloak",
    "api",
    "web",
    "migrate",
    "bioinfo-worker",
    "scientific-scheduler",
    "caddy",
}
IMAGE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:/-]*@sha256:[a-f0-9]{64}$")
REPO = Path(__file__).resolve().parents[2]
NETWORKS = {
    "postgres": {"data"},
    "redis": {"data"},
    "object-store": {"data"},
    "migrate": {"data"},
    "bioinfo-worker": {"data"},
    "scientific-scheduler": {"data"},
    "keycloak": {"application", "data"},
    "api": {"application", "data", "egress"},
    "web": {"application", "egress"},
    "caddy": {"ingress", "application"},
}
VOLUMES = {
    "postgres": {"postgres_data": "/var/lib/postgresql/data"},
    "redis": {"redis_data": "/data"},
    "object-store": {"object_data": "/data"},
    "caddy": {"caddy_data": "/data", "caddy_config": "/config"},
}
SECRET_KEYS = {
    "postgres": ["POSTGRES_PASSWORD"],
    "redis": ["REDISCLI_AUTH"],
    "object-store": ["MINIO_ROOT_USER", "MINIO_ROOT_PASSWORD"],
    "keycloak": ["KC_DB_PASSWORD"],
    "web": ["NEXTAUTH_SECRET", "KEYCLOAK_CLIENT_SECRET"],
    "api": ["OBJECT_STORAGE_ACCESS_KEY", "OBJECT_STORAGE_SECRET_KEY"],
    "migrate": ["OBJECT_STORAGE_ACCESS_KEY", "OBJECT_STORAGE_SECRET_KEY"],
}


def strong(value: object) -> bool:
    text = str(value or "")
    return len(text) >= 20 and not any(
        marker in text.lower()
        for marker in (
            "change-me",
            "change_me",
            "placeholder",
            "development",
            "test-only",
            "${",
            "example",
        )
    )


def validate(config: dict) -> list[str]:
    errors: set[str] = set()

    def require(condition: bool, rule: str) -> None:
        if not condition:
            errors.add(rule)

    project = config.get("name", "")
    require(
        bool(re.fullmatch(r"oligospace-pilot-[a-z0-9][a-z0-9-]*", project)), "project"
    )
    services = config.get("services", {})
    require(set(services) == SERVICES, "service_set")
    for name, service in services.items():
        require(bool(IMAGE.fullmatch(service.get("image", ""))), "image_digest")
        for forbidden in (
            "build",
            "network_mode",
            "container_name",
            "privileged",
            "devices",
            "cap_add",
            "volumes_from",
            "extends",
            "env_file",
            "entrypoint",
            "extra_hosts",
            "pid",
            "ipc",
        ):
            require(not service.get(forbidden), "unsafe_service_option")
        require(not service.get("ports") or name == "caddy", "internal_port")
        require(
            set(service.get("networks", [])) == NETWORKS.get(name, set()),
            "network_membership",
        )
        env = service.get("environment", {})
        require(isinstance(env, dict), "environment_format")
        if not isinstance(env, dict):
            continue
        require(not any("DEVELOPMENT" in key for key in env), "development_parameter")
        for key in SECRET_KEYS.get(name, []):
            require(strong(env.get(key)), "secret_required")
        if name in ("api", "migrate", "web"):
            require(env.get("AUTH_MODE") == "oidc", "auth_mode")
        if name in ("api", "migrate"):
            require(
                env.get("ENVIRONMENT") == "production"
                and str(env.get("UPLOADS_ENABLED")).lower() == "false",
                "production_uploads",
            )
        actual_volumes = {}
        for volume in service.get("volumes", []):
            if isinstance(volume, str):
                source, target = volume.split(":", 1)
                volume = {"type": "volume", "source": source, "target": target}
            source, target = volume.get("source", ""), volume.get("target", "")
            if volume.get("type") == "bind":
                expected = {
                    "caddy": "/etc/caddy/Caddyfile",
                    "keycloak": "/etc/oligospace/keycloak.conf",
                }
                path = Path(source)
                require(
                    target == expected.get(name)
                    and bool(volume.get("read_only"))
                    and path.is_absolute()
                    and not path.resolve().is_relative_to(REPO),
                    "bind_config_only",
                )
            else:
                actual_volumes[source] = target
        require(actual_volumes == VOLUMES.get(name, {}), "volume_mounts")
    for kind in ("volumes", "networks"):
        for key, value in config.get(kind, {}).items():
            value = value or {}
            require(
                not value.get("external")
                and value.get("name", f"{project}_{key}") == f"{project}_{key}",
                "project_resource",
            )
            require(
                not value.get("driver_opts")
                and value.get("driver", "local" if kind == "volumes" else "bridge")
                == ("local" if kind == "volumes" else "bridge"),
                "resource_driver",
            )
            require(
                set(value)
                <= (
                    {"name", "driver", "labels"}
                    if kind == "volumes"
                    else {"name", "driver", "labels", "internal", "ipam"}
                )
                and not value.get("ipam"),
                "resource_options",
            )
    require(
        set(config.get("volumes", {}))
        == {"postgres_data", "redis_data", "object_data", "caddy_data", "caddy_config"},
        "volume_set",
    )
    require(
        set(config.get("networks", {})) == {"application", "data", "egress", "ingress"},
        "network_set",
    )
    for key in ("data", "application"):
        require(
            config.get("networks", {}).get(key, {}).get("internal") is True,
            "private_network",
        )
    if set(services) != SERVICES:
        return sorted(errors)
    envs = {name: services[name].get("environment", {}) for name in SERVICES}
    require(services["api"]["image"] == services["migrate"]["image"], "migration_image")
    require(
        services["bioinfo-worker"]["image"]
        == services["scientific-scheduler"]["image"],
        "scheduler_image",
    )
    require(
        services["migrate"].get("command")
        == ["micromamba", "run", "--name", "base", "alembic", "upgrade", "head"],
        "migration_command",
    )
    require(
        services["keycloak"].get("command")
        == ["--config-file=/etc/oligospace/keycloak.conf", "start"],
        "keycloak_production",
    )
    ports = services["caddy"].get("ports", [])
    require(len(ports) == 1, "ingress_port")
    for port in ports:
        try:
            ip = ipaddress.ip_address(port.get("host_ip", ""))
            require(
                not ip.is_unspecified and not ip.is_global and not ip.is_multicast,
                "ingress_binding",
            )
            require(
                port.get("target") == 443
                and str(port.get("published")) == "443"
                and port.get("protocol", "tcp") == "tcp",
                "ingress_port",
            )
        except (ValueError, AttributeError):
            errors.add("ingress_binding")
    origin = envs["web"].get("NEXTAUTH_URL", "")
    parsed = urlparse(origin)
    require(
        parsed.scheme == "https"
        and bool(parsed.hostname)
        and not parsed.username
        and not parsed.query
        and not parsed.fragment
        and parsed.path in ("", "/"),
        "https_origin",
    )
    issuer = envs["web"].get("KEYCLOAK_ISSUER", "")
    require(
        issuer.startswith(origin.rstrip("/") + "/realms/")
        and envs["api"].get("OIDC_ISSUER") == issuer
        and envs["migrate"].get("OIDC_ISSUER") == issuer,
        "oidc_issuer",
    )
    require(
        envs["api"].get("CORS_ORIGINS") == json.dumps([origin], separators=(",", ":"))
        and envs["keycloak"].get("KC_HOSTNAME") == origin,
        "canonical_origin",
    )
    require(
        bool(envs["api"].get("OIDC_AUDIENCE"))
        and bool(envs["web"].get("KEYCLOAK_CLIENT_ID")),
        "oidc_parameters",
    )
    users = []
    for name in ("api", "migrate", "bioinfo-worker"):
        db = urlparse(envs[name].get("DATABASE_URL", ""))
        users.append(db.username)
        require(
            db.hostname == "postgres"
            and db.path == "/oligospace"
            and strong(db.password)
            and db.username not in (None, "postgres", "oligospace"),
            "database_credential",
        )
    require(
        len(set(users)) == 3
        and envs["scientific-scheduler"].get("DATABASE_URL")
        == envs["bioinfo-worker"].get("DATABASE_URL"),
        "database_role_separation",
    )
    return sorted(errors)


def main() -> int:
    try:
        errors = validate(json.load(sys.stdin))
    except (ValueError, TypeError, KeyError, AttributeError):
        errors = ["invalid_configuration"]
    # Stable rule IDs only: do not echo input values, exception strings or secrets.
    print(
        json.dumps(
            {
                "static": "failed" if errors else "passed",
                "rules": errors,
                "runtime_unverified": [
                    "storage",
                    "tls_oidc_mfa",
                    "rls",
                    "threat_model",
                    "scans",
                    "restore",
                    "capacity",
                    "native_architectures",
                ],
            }
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
