import copy
import unittest
from test_policy import resolved_fixture
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from policy import validate


class PilotSecurityTests(unittest.TestCase):
    def test_all_services_are_bounded_and_nonroot(self):
        c = resolved_fixture()
        self.assertEqual(validate(c), [])
        for name, s in c["services"].items():
            self.assertNotEqual(str(s.get("user", "0")).split(":")[0], "0", name)
            self.assertGreater(s.get("pids_limit", 0), 0, name)
            self.assertTrue(s.get("mem_limit"), name)
            self.assertTrue(s.get("cpus"), name)
            self.assertEqual(s.get("logging", {}).get("driver"), "json-file", name)

    def test_security_mutations_are_refused(self):
        base = resolved_fixture()
        for key, value in [
            ("user", "0:0"),
            ("read_only", False),
            ("pids_limit", 0),
            ("mem_limit", None),
            ("security_opt", []),
            ("cap_drop", []),
            ("logging", {}),
        ]:
            c = copy.deepcopy(base)
            c["services"]["api"][key] = value
            with self.subTest(key=key):
                self.assertTrue(validate(c))

    def test_canonical_project_is_allowed(self):
        c = resolved_fixture()
        c["name"] = "oligospace-pilot"
        self.assertNotIn("project", validate(c))

    def test_jwks_blocker_never_disappears_from_activation(self):
        from doctor import mandatory_blockers

        self.assertIn("AUTH_B6", mandatory_blockers())

    def test_proxy_realm_and_broker_credentials_are_consistent(self):
        base = resolved_fixture()
        changed = copy.deepcopy(base)
        changed["services"]["caddy"]["environment"]["OIDC_REALM"] = "master"
        self.assertIn("canonical_realm", validate(changed))
        changed = copy.deepcopy(base)
        changed["services"]["bioinfo-worker"]["environment"]["REDIS_URL"] = (
            "redis://redis:6379/0"
        )
        self.assertIn("broker_credentials", validate(changed))

    def test_caddy_has_only_its_required_file_capability(self):
        c = resolved_fixture()
        self.assertEqual(c["services"]["caddy"].get("cap_add"), ["NET_BIND_SERVICE"])
        c["services"]["caddy"]["cap_add"] = ["NET_ADMIN"]
        self.assertIn("capability_boundary", validate(c))
