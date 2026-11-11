"""Safety contracts for the explicit disposable production-topology adapter."""

import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / "qualify_pilot.py"
spec = importlib.util.spec_from_file_location("qualify_pilot", PATH)
pilot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pilot)


class PilotQualificationTests(unittest.TestCase):
    def test_requires_explicit_disposable_project_before_docker(self):
        with patch.object(pilot, "captured") as execute:
            for project in ("oligospace-pilot", "production", "oligospace-pilot-test"):
                with (
                    self.subTest(project=project),
                    self.assertRaisesRegex(ValueError, "disposable_project_required"),
                ):
                    pilot.prepare({}, Path("/does-not-exist"), project, {}, "unused")
            execute.assert_not_called()

    def test_interpolation_keeps_secrets_data_and_rejects_missing(self):
        template = '{"environment":{"SECRET":"${PASSWORD:?required outside Git}"}}'
        value = '"\n${OTHER}\\private'
        self.assertEqual(
            pilot.interpolate(template, {"PASSWORD": value})["environment"]["SECRET"],
            value,
        )
        with self.assertRaisesRegex(ValueError, "pilot_fixture_variable_missing"):
            pilot.interpolate(template, {})

    def test_only_real_local_sha256_config_ids_are_accepted(self):
        for result in (
            "image:latest",
            "sha256:" + "f" * 63,
            "registry/x@sha256:" + "f" * 64,
            "sensitive diagnostic",
        ):
            with (
                patch.object(pilot, "captured", return_value=result),
                self.assertRaisesRegex(ValueError, "immutable_local_image_required"),
            ):
                pilot.image_id("reference")
        with patch.object(pilot, "captured", return_value="sha256:" + "a" * 64):
            self.assertEqual(pilot.image_id("reference"), "sha256:" + "a" * 64)

    def test_command_failures_never_echo_captured_credentials(self):
        import subprocess

        with patch.object(
            pilot.subprocess,
            "run",
            return_value=subprocess.CompletedProcess(
                [], 1, "secret-token", "private-dsn"
            ),
        ):
            with self.assertRaisesRegex(
                RuntimeError, "^pilot_qualification_command_failed$"
            ):
                pilot.captured(["false"])

    def test_resolves_real_template_before_disposable_overlay(self):
        # Actual policy, template and generated secrets; only Docker is mocked.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "certs").mkdir()
            (root / "certs/key.pem").write_text("synthetic test key")
            (root / "certs/ca.pem").write_text("synthetic test certificate")
            password = "generated-test-credential-" + "x" * 32
            api = {
                "OIDC_ISSUER": "https://auth-qualification.test/realms/qualification",
                "OIDC_CLIENT_SECRET": password,
                "OBJECT_STORAGE_ACCESS_KEY": password,
                "OBJECT_STORAGE_SECRET_KEY": password,
            }
            legacy = {
                "services": {
                    name: {"build": {"dockerfile": "unused"}, "environment": {}}
                    for name in ("api", "web", "browser", "bioinfo-worker")
                }
            }
            legacy["services"]["api"]["environment"] = api
            legacy["services"]["web"]["environment"] = {"NEXTAUTH_SECRET": password}

            def execute(command, data=None):
                if command[:3] == ["docker", "image", "inspect"]:
                    return "sha256:" + "a" * 64
                if command[0] == "git":
                    return "b" * 40
                return ""

            with patch.object(pilot, "captured", side_effect=execute):
                result = pilot.prepare(
                    legacy,
                    root,
                    "oligospace-pilot-test-fixture",
                    {"database_password": password},
                    password,
                )
            base = json.loads((root / "pilot-qualified-template.json").read_text())
            self.assertEqual(
                set(base["services"]),
                {
                    "postgres",
                    "migrate",
                    "redis",
                    "object-store",
                    "keycloak",
                    "api",
                    "web",
                    "bioinfo-worker",
                    "scientific-scheduler",
                    "caddy",
                },
            )
            self.assertEqual(
                base["services"]["keycloak"]["command"],
                ["--config-file=/etc/oligospace/keycloak.conf", "start"],
            )
            self.assertEqual(
                result["services"]["keycloak"]["command"],
                base["services"]["keycloak"]["command"],
            )
            self.assertEqual(
                base["services"]["keycloak"]["environment"]["KC_DB"], "postgres"
            )
            self.assertNotIn("ports", result["services"]["caddy"])
            self.assertEqual(
                result["services"]["browser"]["environment"]["PILOT_STRICT_TLS"], "1"
            )
            self.assertNotIn(
                "KC_BOOTSTRAP_ADMIN_PASSWORD",
                base["services"]["keycloak"]["environment"],
            )
            self.assertEqual(root.stat().st_mode & 0o777, 0o700)

    def test_proxy_trust_is_narrowed_to_actual_application_subnet(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "compose.json"
            config.write_text(
                json.dumps(
                    {
                        "name": "oligospace-pilot-test-safe",
                        "services": {
                            "keycloak": {
                                "environment": {
                                    "KC_PROXY_TRUSTED_ADDRESSES": "172.18.0.0/16"
                                }
                            }
                        },
                    }
                )
            )
            dc = ["docker", "compose", "--file", str(config)]
            with patch.object(pilot, "captured", side_effect=["", "172.29.0.0/16"]):
                pilot.narrow_proxy_trust(dc)
            self.assertEqual(
                json.loads(config.read_text())["services"]["keycloak"]["environment"][
                    "KC_PROXY_TRUSTED_ADDRESSES"
                ],
                "172.29.0.0/16",
            )
            for subnet in ("0.0.0.0/0", "10.0.0.0/8", "8.8.8.0/24"):
                with (
                    self.subTest(subnet=subnet),
                    patch.object(pilot, "captured", side_effect=["", subnet]),
                    self.assertRaisesRegex(
                        ValueError, "private_application_subnet_required"
                    ),
                ):
                    pilot.narrow_proxy_trust(dc)

    def test_network_probe_has_only_ingress_and_no_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / "compose.json"
            config.write_text(
                json.dumps(
                    {
                        "services": {
                            "migrate": {
                                "image": "sha256:" + "a" * 64,
                                "networks": ["data"],
                                "environment": {"DATABASE_URL": "private-dsn"},
                            }
                        }
                    }
                )
            )
            dc = ["docker", "compose", "--file", str(config)]
            with patch.object(pilot, "captured"):
                pilot.network_probe(dc, root)
            probe = json.loads((root / "probe.json").read_text())["services"][
                "untrusted-probe"
            ]
            self.assertEqual(probe["networks"], ["ingress"])
            self.assertEqual(probe["environment"], {})
            self.assertNotIn("private-dsn", json.dumps(probe))


if __name__ == "__main__":
    unittest.main()
