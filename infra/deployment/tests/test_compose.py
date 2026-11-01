from pathlib import Path
import re
import subprocess
import tempfile
import unittest

from test_policy import ROOT


class ComposeTests(unittest.TestCase):
    def test_real_compose_resolution_then_policy(self):
        template = (ROOT / "compose.pilot.json").read_text()
        # Resolve only public test fixtures into an external mode-0600 env file.
        keys = set(re.findall(r"\$\{([A-Z0-9_]+):\?[^}]+\}", template))
        from test_policy import fixture_value

        with tempfile.TemporaryDirectory(
            prefix="oligospace-deploy01-config-"
        ) as directory:
            env = Path(directory) / "test.env"
            env.write_text(
                "\n".join(key + "=" + fixture_value(key) for key in sorted(keys))
            )
            env.chmod(0o600)
            result = subprocess.run(
                [
                    "docker",
                    "compose",
                    "--project-name",
                    "oligospace-pilot-test-policy",
                    "--env-file",
                    str(env),
                    "--file",
                    str(ROOT / "compose.pilot.json"),
                    "--profile",
                    "operations",
                    "config",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(
                result.returncode, 0, "Compose resolution failed (details suppressed)"
            )
            policy = subprocess.run(
                ["python3", str(ROOT / "policy.py")],
                input=result.stdout,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(policy.returncode, 0, policy.stdout)
            self.assertNotIn(
                "isolated-generated-test-credential", policy.stdout + policy.stderr
            )


if __name__ == "__main__":
    unittest.main()
