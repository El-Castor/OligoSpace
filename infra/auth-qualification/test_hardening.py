"""Hardened qualification preserves isolation, including disposable fault injection."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import run


class HardenedQualificationTests(unittest.TestCase):
    def test_runtime_constraints_preserve_ca_and_image_user(self):
        compose = {
            "networks": {"default": {"internal": True}},
            "services": {
                name: {"volumes": ["/private/ca:/certs/ca.pem:ro"]}
                for name in ("api", "bioinfo-worker", "scientific-scheduler")
            },
        }
        run.harden_compose(compose)
        self.assertTrue(compose["networks"]["default"]["internal"])
        for service in compose["services"].values():
            self.assertTrue(service["read_only"])
            self.assertEqual(service["cap_drop"], ["ALL"])
            self.assertEqual(service["security_opt"], ["no-new-privileges:true"])
            self.assertEqual(service["pids_limit"], 256)
            self.assertIn("size=128m", service["tmpfs"][0])
            self.assertIn("noexec", service["tmpfs"][0])
            self.assertEqual(service["volumes"], ["/private/ca:/certs/ca.pem:ro"])
            self.assertNotIn("user", service)
            self.assertNotIn("ports", service)
        scheduler = compose["services"]["scientific-scheduler"]["command"]
        self.assertEqual(scheduler[0], "celery")
        self.assertIn("--schedule=/tmp/celerybeat-schedule", scheduler)

    def test_fault_recreation_only_changes_readonly_primer3_mount(self):
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary)
            original = {
                "services": {
                    "bioinfo-worker": {
                        "read_only": True,
                        "volumes": ["ca:/certs/ca.pem:ro"],
                    }
                }
            }
            config = work / "compose.json"
            config.write_text(json.dumps(original))
            dc = [
                "docker",
                "compose",
                "--project-name",
                "disposable",
                "--file",
                str(config),
            ]
            fault = run.hardened_worker_action(dc, work / "evidence", fault=True)
            changed = json.loads(Path(fault[fault.index("--file") + 1]).read_text())
            mounts = changed["services"]["bioinfo-worker"]["volumes"]
            self.assertEqual(mounts[0], "ca:/certs/ca.pem:ro")
            self.assertEqual(
                mounts[1],
                f"{work / 'primer3-failure'}:/opt/primer3/bin/primer3_core:ro",
            )
            self.assertTrue(changed["services"]["bioinfo-worker"]["read_only"])
            self.assertEqual(json.loads(config.read_text()), original)
            self.assertEqual(
                (work / "primer3-failure").read_text(), "#!/bin/sh\nexit 1\n"
            )
            self.assertEqual(
                run.hardened_worker_action(dc, work / "evidence", fault=False),
                dc
                + ["up", "--detach", "--no-deps", "--force-recreate", "bioinfo-worker"],
            )
            self.assertNotIn("exec", fault)
            self.assertNotIn("--user", fault)

    def test_fault_refuses_fixture_outside_private_workdir(self):
        with self.assertRaises(ValueError):
            run.hardened_worker_action(
                ["docker", "compose", "--file", "/private/a/compose.json"],
                Path("/private/b/evidence"),
                fault=True,
            )

    def test_hardened_signal_acknowledges_only_successful_recreation(self):
        for code, expected in ((0, "ok"), (1, "failed")):
            with (
                self.subTest(returncode=code),
                tempfile.TemporaryDirectory() as temporary,
            ):
                work = Path(temporary)
                signals = work / "evidence"
                signals.mkdir()
                (signals / "worker-fault-request").touch()
                config = work / "compose.json"
                config.write_text(
                    json.dumps({"services": {"bioinfo-worker": {"read_only": True}}})
                )
                dc = ["docker", "compose", "--file", str(config)]
                process = Mock()
                process.poll.side_effect = [None, 0]
                with (
                    patch.object(run, "HARDENED", True),
                    patch.object(
                        run.subprocess, "run", return_value=Mock(returncode=code)
                    ) as execute,
                    patch.object(run.time, "sleep"),
                ):
                    run.serve_outage_signals(dc, signals, process)
                self.assertEqual((signals / "worker-fault-ack").read_text(), expected)
                command = execute.call_args.args[0]
                self.assertIn("--force-recreate", command)
                self.assertNotIn("exec", command)
                self.assertNotIn("root", command)
