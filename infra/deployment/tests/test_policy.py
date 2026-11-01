"""Executable fail-closed policy regressions; fixture digests are NOT artifacts."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


def resolved_fixture():
    """Docker-free interpolation only for policy tests, never runtime evidence."""
    import re

    text = (ROOT / "compose.pilot.json").read_text()
    return json.loads(
        re.sub(r"\$\{([A-Z0-9_]+):\?[^}]+\}", lambda m: fixture_value(m.group(1)), text)
    )


def fixture_value(key):
    values = {
        "PILOT_PROJECT": "oligospace-pilot-test-policy",
        "APP_ORIGIN": "https://pilot.invalid",
        "OIDC_ISSUER": "https://pilot.invalid/realms/oligospace",
        "OIDC_CLIENT_ID": "oligospace-web",
        "OIDC_AUDIENCE": "oligospace-api",
        "TLS_CONFIG": "/qualified/Caddyfile",
        "KEYCLOAK_CONFIG": "/qualified/keycloak.conf",
        "BUILD_ID": "a" * 40,
        "INGRESS_IP": "127.0.0.1",
    }
    if key.endswith("_IMAGE"):
        return "registry.invalid/test/" + key.lower() + "@sha256:" + "a" * 64
    if key.endswith("DATABASE_URL"):
        user = key.lower().removesuffix("_database_url")
        return (
            "postgresql+asyncpg://"
            + user
            + ":isolated-generated-test-credential-7ab293bd@postgres/oligospace"
        )
    return values.get(key, "isolated-generated-test-credential-7ab293bd")


class PolicyTests(unittest.TestCase):
    def check_config(self, config):
        result = subprocess.run(
            [sys.executable, str(ROOT / "policy.py")],
            input=json.dumps(config),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotIn(
            "isolated-generated-test-credential", result.stdout + result.stderr
        )
        return result

    def test_independent_template_is_structurally_safe(self):
        result = self.check_config(resolved_fixture())
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("runtime_unverified", result.stdout)

    def test_unsafe_mutations_are_refused(self):
        base = resolved_fixture()

        def image(c):
            c["services"]["web"]["image"] = "example/web:latest"

        def port(c):
            c["services"]["postgres"]["ports"] = ["5432:5432"]

        def auth(c):
            c["services"]["api"]["environment"]["AUTH_MODE"] = "development"

        def devkc(c):
            c["services"]["keycloak"]["command"] = ["start-dev"]

        def seed(c):
            c["services"]["seed"] = copy.deepcopy(c["services"]["migrate"])

        def bind(c):
            c["services"]["web"]["volumes"] = ["../../apps/web:/app"]

        def volume(c):
            c["volumes"]["postgres_data"] = {
                "external": True,
                "name": "oligospace_postgres_data",
            }

        def migration(c):
            c["services"]["migrate"]["image"] = c["services"]["web"]["image"]

        def secret(c):
            c["services"]["web"]["environment"]["NEXTAUTH_SECRET"] = "change-me"

        def origin(c):
            c["services"]["web"]["environment"]["NEXTAUTH_URL"] = "http://pilot.invalid"

        def upload(c):
            c["services"]["api"]["environment"]["UPLOADS_ENABLED"] = "true"

        def escape(c):
            c["services"]["web"]["network_mode"] = "host"

        def share(c):
            c["services"]["bioinfo-worker"]["environment"]["DATABASE_URL"] = c[
                "services"
            ]["api"]["environment"]["DATABASE_URL"]

        def hidden_bind(c):
            c["volumes"]["postgres_data"]["driver_opts"] = {
                "type": "none",
                "o": "bind",
                "device": "/existing/database",
            }

        for mutation in (
            image,
            port,
            auth,
            devkc,
            seed,
            bind,
            volume,
            migration,
            secret,
            origin,
            upload,
            escape,
            share,
            hidden_bind,
        ):
            with self.subTest(mutation=mutation.__name__):
                config = copy.deepcopy(base)
                mutation(config)
                self.assertNotEqual(self.check_config(config).returncode, 0)

    def test_invalid_input_never_echoes_payload(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "policy.py")],
            input="sensitive-unparseable-value",
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("sensitive-unparseable-value", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
