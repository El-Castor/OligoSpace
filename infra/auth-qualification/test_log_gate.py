"""Secret-log gate checks use synthetic RAM-only inputs and temporary output."""

import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

import run


class LogGateTests(unittest.TestCase):
    def inspect(self, logs: bytes, retrieval_rule: str | None = None):
        with tempfile.TemporaryDirectory() as temporary:
            evidence = Path(temporary)
            with patch.object(
                run, "capture_service_logs", return_value=(logs, retrieval_rule)
            ):
                gate = run.check_log_secrets(
                    [], {"client_secret": "synthetic-sensitive-value"}, evidence
                )
            return gate, json.loads((evidence / "secret-log-gate.json").read_text())

    def test_generated_secret_fails_without_retaining_its_value(self):
        gate, report = self.inspect(b"synthetic-sensitive-value")
        self.assertEqual(gate, "failed")
        self.assertNotIn("synthetic-sensitive-value", json.dumps(report))
        self.assertEqual(report["services"][0]["findings"][0]["count"], 1)

    def test_jwt_shaped_material_fails_without_retaining_segments(self):
        token = b".".join([b"a" * 20, b"b" * 20, b"c" * 20])
        gate, report = self.inspect(token)
        self.assertEqual(gate, "failed")
        self.assertNotIn(token.decode(), json.dumps(report))
        self.assertEqual(
            report["services"][0]["findings"][0]["rule_id"], "JWT_LIKE_TOKEN_PRESENT"
        )

    def test_public_version_strings_pass(self):
        gate, _ = self.inspect(b"Keycloak 26.7.2; Caddy 2.11.4; Next.js 16.4.1")
        self.assertEqual(gate, "passed")

    def test_incomplete_log_retrieval_never_passes(self):
        for rule in (
            "LOG_RETRIEVAL_FAILED",
            "LOG_RETRIEVAL_TIMEOUT",
            "LOG_LIMIT_EXCEEDED",
        ):
            with self.subTest(rule=rule):
                gate, _ = self.inspect(b"", rule)
                self.assertEqual(gate, "not_verified")

    def test_detected_secret_remains_failed_when_retrieval_is_incomplete(self):
        gate, _ = self.inspect(b"synthetic-sensitive-value", "LOG_LIMIT_EXCEEDED")
        self.assertEqual(gate, "failed")

    def test_capture_caps_ram_and_refuses_truncated_logs(self):
        logs, rule = run.capture_service_logs(
            [
                sys.executable,
                "-c",
                "import sys; sys.stdout.buffer.write(b'x'*(4*1024*1024+1))",
            ]
        )
        self.assertLessEqual(len(logs), 4 * 1024 * 1024)
        self.assertEqual(rule, "LOG_LIMIT_EXCEEDED")


class RealmAudienceContractTests(unittest.TestCase):
    def test_token_audiences_cover_api_and_confidential_introspector(self):
        import json
        from pathlib import Path

        realm = json.loads(
            (
                Path(__file__).resolve().parents[1] / "keycloak/realm-oligospace.json"
            ).read_text()
        )
        client = next(
            item for item in realm["clients"] if item["clientId"] == "oligospace-web"
        )
        audiences = {
            mapper["config"].get("included.client.audience")
            for mapper in client["protocolMappers"]
            if mapper["protocolMapper"] == "oidc-audience-mapper"
            and mapper["config"].get("access.token.claim") == "true"
        }
        self.assertIn("oligospace-api", audiences)
        self.assertIn(client["clientId"], audiences)
        self.assertNotEqual(
            client.get("attributes", {}).get(
                "allow.token.introspection.without.audience.check"
            ),
            "true",
        )


if __name__ == "__main__":
    unittest.main()
