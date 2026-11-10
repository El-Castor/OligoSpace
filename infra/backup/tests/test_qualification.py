"""Evidence collection contracts for the real disposable recovery harness."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location(
    "recovery_qualification", ROOT / "qualify.py"
)
qualification = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qualification)


class QualificationEvidenceTests(unittest.TestCase):
    def test_s3_failure_diagnostic_never_retains_message_or_resource(self):
        from minio.error import S3Error

        for code, expected in (
            ("NoSuchBucket", "NoSuchBucket"),
            ("private-code", "other"),
        ):
            error = S3Error(
                response=None,
                code=code,
                message="private-message",
                resource="private-resource",
                request_id="private-request",
                host_id="private-host",
            )
            diagnostic = qualification.exception_diagnostic(error)
            self.assertEqual(
                diagnostic, {"exception_type": "S3Error", "s3_code": expected}
            )
            self.assertNotIn("private", json.dumps(diagnostic))

    def test_unknown_exception_class_is_not_written_to_evidence(self):
        private_class = type("PrivateCredentialClass", (Exception,), {})
        self.assertEqual(
            qualification.exception_diagnostic(private_class("private-message")),
            {"exception_type": "other"},
        )

    def test_disposable_storage_selection_keeps_pinned_variant_and_private_parent(self):
        from storage_profiles import IMAGES, QUALIFICATION_VARIANTS

        values = {
            label: "generated-synthetic-only"
            for label in (
                "database",
                "app_database",
                "worker_database",
                "identity_database",
                "password",
                "client",
                "bootstrap",
                "storage_access",
                "storage_secret",
            )
        }
        for kind, image, port, config in (
            ("seaweedfs", QUALIFICATION_VARIANTS["seaweedfs-4.52"], 8333, "s3.json"),
            ("garage", IMAGES["garage"], 3900, "garage.toml"),
        ):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                stack = qualification.Stack(root, "default", "target", values, {}, kind)
                compose = json.loads(stack.compose_file.read_text())
                service = compose["services"]["s3"]
                self.assertEqual(service["image"], image)
                self.assertEqual(service["ports"], [f"127.0.0.1::{port}"])
                self.assertTrue(
                    any(
                        config in mount and mount.endswith(":ro")
                        for mount in service["volumes"]
                    )
                )
                self.assertEqual(root.stat().st_mode & 0o777, 0o700)
                self.assertEqual(stack.storage_port, port)
                if kind == "seaweedfs":
                    self.assertFalse(service["environment"])
                    self.assertEqual(
                        (stack.root / config).stat().st_mode & 0o777, 0o644
                    )
                    self.assertIn(
                        "-s3.config=/etc/seaweedfs/s3.json", service["command"]
                    )
                    advertised = next(
                        value[4:]
                        for value in service["command"]
                        if value.startswith("-ip=")
                    )
                    self.assertEqual(service["container_name"], advertised)
                    self.assertTrue(advertised.startswith(stack.project))

    def test_storage_credentials_never_get_readable_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            root.chmod(0o755)
            with self.assertRaisesRegex(
                qualification.QualificationError, "private_fixture_root_required"
            ):
                qualification.Stack(root, "default", "target", {}, {})
            self.assertFalse((root / "target").exists())

    def test_secret_log_diagnostic_reports_labels_not_values(self):
        labels = (
            "database",
            "app_database",
            "worker_database",
            "identity_database",
            "password",
            "client",
            "bootstrap",
            "storage_access",
            "storage_secret",
        )
        values = {label: "private-value-for-" + label + "-end" for label in labels}

        def logs(*args):
            return (
                values["identity_database"].encode() if args[-1] == "postgres" else b""
            )

        stack = SimpleNamespace(side="source", storage_secrets=["private-rpc"], dc=logs)
        retrievals, findings = qualification.check_secret_logs((stack,), values)
        self.assertEqual(len(retrievals), 7)
        self.assertTrue(all(item["status"] == "passed" for item in retrievals))
        self.assertEqual(
            findings,
            [
                {
                    "side": "source",
                    "service": "postgres",
                    "secret_label": "identity_database",
                }
            ],
        )
        self.assertNotIn("private", json.dumps([retrievals, findings]))

    def test_secret_log_retrieval_failure_remains_explicit(self):
        values = {
            label: "private-value-for-" + label + "-end"
            for label in (
                "database",
                "app_database",
                "worker_database",
                "identity_database",
                "password",
                "client",
                "bootstrap",
                "storage_access",
                "storage_secret",
            )
        }

        def failed(*args):
            raise RuntimeError("private-error-body")

        stack = SimpleNamespace(side="target", storage_secrets=[], dc=failed)
        retrievals, findings = qualification.check_secret_logs((stack,), values)
        self.assertEqual(len(retrievals), 7)
        self.assertTrue(all(item["status"] == "failed" for item in retrievals))
        self.assertFalse(findings)
        self.assertNotIn("private", json.dumps(retrievals))

    def test_loopback_ingress_is_separate_from_internal_data_network(self):
        with tempfile.TemporaryDirectory() as directory:
            values = {
                name: "synthetic"
                for name in (
                    "database",
                    "app_database",
                    "worker_database",
                    "identity_database",
                    "client",
                    "bootstrap",
                    "password",
                    "storage_access",
                    "storage_secret",
                )
            }
            stack = qualification.Stack(
                Path(directory), "default", "target", values, {}
            )
            compose = json.loads(stack.compose_file.read_text())
            self.assertTrue(compose["networks"]["default"]["internal"])
            ingress = compose["networks"]["qualification_ingress"]
            self.assertEqual(
                ingress["driver_opts"]["com.docker.network.bridge.host_binding_ipv4"],
                "127.0.0.1",
            )
            participants = {
                name
                for name, service in compose["services"].items()
                if "qualification_ingress" in service.get("networks", [])
            }
            self.assertEqual(participants, {"api", "keycloak", "s3"})
            for name in participants:
                self.assertEqual(
                    set(compose["services"][name]["networks"]),
                    {"default", "qualification_ingress"},
                )
                self.assertTrue(
                    all(
                        port.startswith("127.0.0.1::")
                        for port in compose["services"][name]["ports"]
                    )
                )
            for name in ("postgres", "redis", "bioinfo-worker", "scientific-scheduler"):
                self.assertFalse(compose["services"][name].get("ports"))
                self.assertNotIn(
                    "qualification_ingress",
                    compose["services"][name].get("networks", []),
                )

    def test_successful_log_retrieval_includes_stderr(self):
        # A service leaking on stderr must be visible to the log gate as well.
        actual = qualification.execute(
            [
                sys.executable,
                "-c",
                "import sys; print('stdout'); print('stderr-secret',file=sys.stderr)",
            ],
            merge_stderr=True,
        )
        self.assertIn(b"stdout", actual)
        self.assertIn(b"stderr-secret", actual)

    def test_failed_log_retrieval_never_proves_absence(self):
        with self.assertRaisesRegex(
            qualification.QualificationError, "qualification_command_failed"
        ) as error:
            qualification.execute(
                [
                    sys.executable,
                    "-c",
                    "import sys; print('private-credential',file=sys.stderr); sys.exit(2)",
                ],
                merge_stderr=True,
            )
        self.assertNotIn("private-credential", str(error.exception))

    def test_negative_case_must_actually_fail(self):
        with self.assertRaisesRegex(
            qualification.QualificationError,
            "negative_case_did_not_refuse_corrupt_archive",
        ):
            qualification.expect_failure(lambda: None, "corrupt_archive")

    def test_command_timeout_is_never_successful_empty_output(self):
        with patch.object(
            qualification.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired("operation", 1),
        ):
            with self.assertRaises(subprocess.TimeoutExpired):
                qualification.execute(["irrelevant"], merge_stderr=True)

    def test_build_failure_diagnostic_contains_fixed_labels_only(self):
        failed = subprocess.CompletedProcess(
            ["docker", "compose", "build", "api"],
            1,
            stdout=b"private-credential Unable to locate package private-package",
            stderr=b"failed to solve",
        )
        with patch.object(qualification.subprocess, "run", return_value=failed):
            with self.assertRaises(qualification.QualificationError) as error:
                qualification.execute(failed.args)
        self.assertEqual(
            error.exception.diagnostic,
            {"command_phase": "build", "categories": ["build", "apt_index"]},
        )
        self.assertNotIn("private", str(error.exception))
        self.assertNotIn("private", json.dumps(error.exception.diagnostic))

    def test_consistent_object_omission_requires_cross_store_refusal(self):
        import archive
        from recovery import Recovery
        from s3 import validate_export

        with tempfile.TemporaryDirectory() as directory:
            tree = Path(directory)
            (tree / "objects").mkdir()
            payload = tree / "objects/0.bin"
            payload.write_bytes(b"synthetic")
            reference = {
                "object_key": "quarantine/evidence.txt",
                "sha256": archive.digest(payload),
                "size_bytes": 9,
                "content_type": "text/plain",
            }
            manifest = {
                "schema": "oligospace-recovery/v1",
                "attachment_references": [reference],
                "buckets": [
                    {
                        "bucket": "recovery-evidence",
                        "objects": [
                            {
                                "key": reference["object_key"],
                                "file": "objects/0.bin",
                                "sha256": reference["sha256"],
                                "size": 9,
                                "content_type": "text/plain",
                                "metadata": {},
                                "tags": {},
                            }
                        ],
                    }
                ],
                "files": archive.manifest_files(tree),
            }
            (tree / "manifest.json").write_text(json.dumps(manifest))
            qualification.omit_referenced_object(tree)
            incomplete = archive.validate_tree(tree)
            validate_export(incomplete["buckets"], tree)
            self.assertEqual(incomplete["attachment_references"], [reference])
            self.assertEqual(incomplete["buckets"][0]["objects"], [])
            checker = object.__new__(Recovery)
            checker.config = {"buckets": ["recovery-evidence"]}
            with self.assertRaisesRegex(
                ValueError, "attachment_object_integrity_failed"
            ):
                checker._validate_attachment_records(
                    incomplete["attachment_references"], incomplete["buckets"]
                )


if __name__ == "__main__":
    unittest.main()


class StorageEndpointTests(unittest.TestCase):
    def test_api_uses_selected_disposable_storage_port(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            values = {
                name: "x" * 48
                for name in (
                    "database",
                    "app_database",
                    "worker_database",
                    "identity_database",
                    "password",
                    "client",
                    "bootstrap",
                    "storage_access",
                    "storage_secret",
                )
            }
            for kind, port in (("seaweedfs", 8333), ("garage", 3900)):
                side = "target-" + kind
                stack = qualification.Stack(
                    root,
                    "default",
                    side,
                    values,
                    {"admin": "a", "viewer": "v"},
                    storage_kind=kind,
                )
                definition = json.loads(stack.compose_file.read_text())
                self.assertEqual(
                    definition["services"]["api"]["environment"][
                        "OBJECT_STORAGE_ENDPOINT"
                    ],
                    f"s3:{port}",
                )
