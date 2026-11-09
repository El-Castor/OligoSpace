import importlib.util
import json
from pathlib import Path
import sys
import unittest
import subprocess
import tempfile
from unittest.mock import patch
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
spec = importlib.util.spec_from_file_location(
    "scan_artifact", Path(__file__).resolve().parents[1] / "scan_artifact.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
PROOF = {"config_digest": "sha256:" + "a" * 64, "architecture": "arm64"}
DB = {
    "Version": 2,
    **{k: "2026-11-02T00:00:00Z" for k in ("UpdatedAt", "NextUpdate", "DownloadedAt")},
}


def fixture():
    return {
        "SchemaVersion": 2,
        "ArtifactType": "container_image",
        "Metadata": {
            "ImageID": PROOF["config_digest"],
            "ImageConfig": {"architecture": "arm64", "os": "linux"},
            "OS": {"Family": "debian", "Name": "12"},
        },
    }


class ScanTests(unittest.TestCase):
    def test_trivy_cvss40_and_public_github_cve_search_are_retained(self):
        vector = "CVSS:4.0/AV:N/AC:L/AT:P/PR:L/UI:A/VC:N/VI:L/VA:N/SC:N/SI:N/SA:N"
        metrics = {"ghsa": {"V40Vector": vector, "V40Score": 5.3}}
        self.assertEqual(module.public_cvss(metrics), metrics)
        url = "https://github.com/advisories?query=CVE-2026-1234"
        self.assertEqual(module.public_url(url), url)
        for unsafe in (
            "https://github.com/advisories?query=private-token",
            "https://github.com/advisories?query=CVE-2026-1234&token=private",
            "https://example.org/advisories?query=CVE-2026-1234",
        ):
            with self.subTest(url=unsafe), self.assertRaises(ValueError):
                module.public_url(unsafe)

    def test_public_scoring_inventory_and_ubuntu_identity(self):
        raw = fixture()
        raw["Metadata"]["OS"] = {"Family": "ubuntu", "Name": "24.04"}
        raw["Results"] = [
            {
                "Type": "ubuntu",
                "Packages": [
                    {
                        "Name": "libc6",
                        "Version": "2.39",
                        "SrcName": "glibc",
                        "SrcVersion": "2.39",
                    }
                ],
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2026-1234",
                        "Severity": "HIGH",
                        "PkgName": "libc6",
                        "CVSS": {
                            "nvd": {
                                "V3Score": 8.1,
                                "V3Vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:H",
                            }
                        },
                        "SeveritySource": "nvd",
                        "DataSource": {
                            "ID": "ubuntu",
                            "Name": "Ubuntu CVE Tracker",
                            "URL": "https://ubuntu.com/security/",
                        },
                        "PrimaryURL": "https://ubuntu.com/security/CVE-2026-1234",
                        "Layer": {"Digest": "sha256:" + "a" * 64},
                        "PkgPath": "/opt/conda/lib/private-filename",
                    }
                ],
            }
        ]
        report = module.summarize(raw, PROOF, DB)
        row = report["vulnerabilities"][0]
        self.assertEqual(row["cvss"]["nvd"]["V3Score"], 8.1)
        self.assertEqual(row["severity_source"], "nvd")
        self.assertEqual(row["package_path"], "conda_environment_file")
        self.assertNotIn("private-filename", json.dumps(report))
        self.assertEqual(
            report["operating_system"], {"family": "ubuntu", "name": "24.04"}
        )
        self.assertEqual(report["package_inventory"][0]["source_package"], "glibc")
        self.assertEqual(report["package_inventory_coverage"], "observed")
        self.assertEqual(report["gate"], "failed")

    def test_unsafe_public_fields_fail_closed(self):
        for field, value in (
            ("PrimaryURL", "https://user:secret@example.org/a"),
            ("PrimaryURL", "https://example.org/a?token=private"),
            ("CVSS", {"nvd": {"V3Score": 11}}),
            ("Layer", {"Digest": "private"}),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                module.summarize(
                    {
                        **fixture(),
                        "Results": [
                            {
                                "Vulnerabilities": [
                                    {
                                        "VulnerabilityID": "CVE-2026-1234",
                                        "Severity": "HIGH",
                                        field: value,
                                    }
                                ]
                            }
                        ],
                    },
                    PROOF,
                    DB,
                )

    def test_missing_inventory_is_explicit_and_unknown_cvss_is_null(self):
        raw = fixture()
        raw["Results"] = [
            {
                "Vulnerabilities": [
                    {"VulnerabilityID": "CVE-2026-1234", "Severity": "LOW"}
                ]
            }
        ]
        report = module.summarize(raw, PROOF, DB)
        self.assertEqual(report["package_inventory_coverage"], "not_verified")
        self.assertIsNone(report["vulnerabilities"][0]["cvss"])
        with self.assertRaises(ValueError):
            module.summarize(raw, PROOF, DB, require_inventory=True)

    def test_frozen_cli_is_offline_and_rejects_database_mutation(self):
        for mutate in (False, True):
            with (
                self.subTest(mutate=mutate),
                tempfile.TemporaryDirectory() as directory,
            ):
                root = Path(directory)
                (root / "db").mkdir()
                (root / "db/metadata.json").write_text(json.dumps(DB))
                (root / "db/trivy.db").write_bytes(b"original")
                output = root / "output.json"
                raw = fixture()
                raw["Results"] = [
                    {"Type": "debian", "Packages": [{"Name": "libc6", "Version": "1"}]}
                ]
                proof = {**PROOF, "descriptor": {"digest": "sha256:" + "b" * 64}}

                def scan(command, **kwargs):
                    self.assertIn("--offline-scan", command)
                    self.assertIn("--skip-db-update", command)
                    self.assertIn("--list-all-pkgs", command)
                    self.assertEqual(command[command.index("--network") + 1], "none")
                    self.assertIn(str(root.resolve()) + ":/cache:ro", command)
                    if mutate:
                        (root / "db/trivy.db").write_bytes(b"changed")
                    return SimpleNamespace(
                        returncode=0, stdout=json.dumps(raw), stderr=""
                    )

                argv = [
                    "scan",
                    "--context",
                    "test",
                    "--archive",
                    str(root / "archive"),
                    "--source",
                    "a" * 40,
                    "--architecture",
                    "arm64",
                    "--output",
                    str(output),
                    "--vulnerability-cache",
                    str(root),
                ]
                with (
                    patch.object(sys, "argv", argv),
                    patch.object(module, "prepare_layout", return_value=proof),
                    patch.object(
                        module.subprocess,
                        "check_output",
                        return_value=b'[{"Endpoints":{"docker":{"Host":"unix:///synthetic"}}}]',
                    ),
                    patch.object(module.subprocess, "run", side_effect=scan),
                    patch.dict(module.os.environ, {}, clear=True),
                    self.assertRaises(SystemExit) as stopped,
                ):
                    module.main()
                report = json.loads(output.read_text())
                if mutate:
                    self.assertEqual(report["gate"], "not_verified")
                    self.assertEqual(report["rule_id"], "SCAN_FROZEN_DATABASE_CHANGED")
                    self.assertNotEqual(stopped.exception.code, 0)
                else:
                    self.assertEqual(stopped.exception.code, 0)
                    self.assertTrue(
                        report["frozen_vulnerability_database"]["unchanged_after_scan"]
                    )

    def test_frozen_database_requires_complete_files_and_detects_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                module.frozen_database_identity(root)
            (root / "db").mkdir()
            (root / "db/metadata.json").write_text(json.dumps(DB))
            (root / "db/trivy.db").write_bytes(b"database")
            identity = module.frozen_database_identity(root)
            module.verify_frozen_database(root, identity)
            (root / "db/trivy.db").write_bytes(b"changed")
            with self.assertRaises(ValueError):
                module.verify_frozen_database(root, identity)

    def test_vendor_advisory_identifiers_are_retained_and_still_block_release(self):
        raw = fixture()
        raw["Results"] = [
            {
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": identifier,
                        "Severity": "LOW",
                        "PkgName": "synthetic-package",
                        "InstalledVersion": "1.0",
                        "FixedVersion": "",
                    }
                    for identifier in (
                        "TEMP-0000000-ABC123",
                        "RUSTSEC-2026-0001",
                        "DLA-4000-1",
                    )
                ]
            }
        ]
        report = module.summarize(raw, PROOF, DB)
        self.assertEqual(report["execution"], "completed_with_findings")
        self.assertEqual(report["gate"], "failed")
        self.assertEqual(
            report["vulnerability_ids"],
            ["DLA-4000-1", "RUSTSEC-2026-0001", "TEMP-0000000-ABC123"],
        )

    def test_valid_multiple_fixed_versions_remain_blocking_findings(self):
        raw = fixture()
        raw["Results"] = [
            {
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2026-1234",
                        "Severity": "HIGH",
                        "PkgName": "synthetic-package",
                        "InstalledVersion": "1.0",
                        "FixedVersion": "1.2.3, 2.3.4",
                    }
                ]
            }
        ]
        report = module.summarize(raw, PROOF, DB)
        self.assertEqual(report["execution"], "completed_with_findings")
        self.assertEqual(report["gate"], "failed")
        self.assertEqual(report["vulnerabilities"][0]["fixed_version"], "1.2.3, 2.3.4")

    def test_validation_rule_identifies_structure_without_error_payload(self):
        self.assertEqual(
            module.validation_rule(
                "SCAN_REPORT_INVALID", ValueError("report_platform_mismatch")
            ),
            "SCAN_REPORT_PLATFORM_MISMATCH",
        )
        self.assertEqual(
            module.validation_rule(
                "SCAN_REPORT_INVALID", ValueError("sensitive-private-error")
            ),
            "SCAN_REPORT_INVALID",
        )

    def test_invalid_input_reports_scan_not_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "invalid.tar"
            archive.write_bytes(b"not-an-oci-archive")
            output = root / "scan.json"
            script = Path(__file__).resolve().parents[1] / "scan_artifact.py"
            process = subprocess.run(
                [
                    sys.executable,
                    str(script),
                    "--context",
                    "synthetic",
                    "--archive",
                    str(archive),
                    "--source",
                    "a" * 40,
                    "--architecture",
                    "arm64",
                    "--output",
                    str(output),
                ],
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(process.returncode, 0)
            report = json.loads(output.read_text())
            self.assertEqual(report["execution"], "not_executed")
            self.assertEqual(report["gate"], "not_verified")

    def test_failure_diagnostics_expose_only_fixed_categories(self):
        report = module.failure_diagnostics(
            "private-match failed database archive permission denied", 1
        )
        self.assertEqual(
            report["error_categories"], ["archive", "database", "permission denied"]
        )
        self.assertNotIn("private-match", json.dumps(report))

    def test_secret_matches_never_enter_sanitized_reports(self):
        raw = fixture()
        raw["Results"] = [
            {
                "Secrets": [{"Match": "sensitive-test-value", "Code": "private"}],
                "Vulnerabilities": [
                    {
                        "VulnerabilityID": "CVE-2026-1234",
                        "Severity": "HIGH",
                        "PkgName": "openssl",
                        "InstalledVersion": "1.0",
                        "FixedVersion": "2.0",
                    }
                ],
            }
        ]
        report = module.summarize(raw, PROOF, DB)
        for secret in ("sensitive-test-value", "private", "private-url"):
            self.assertNotIn(secret, json.dumps(report))
        self.assertEqual(report["secret_findings"], 1)
        self.assertEqual(report["execution"], "completed_with_findings")
        self.assertEqual(report["gate"], "failed")

    def test_secret_triage_preserves_only_public_rule_and_known_image_path(self):
        raw = fixture()
        raw["Results"] = [
            {
                "Target": "/opt/conda/lib/python3.12/test/certdata/key.pem",
                "Secrets": [
                    {
                        "RuleID": "private-key",
                        "Match": "sensitive-test-value",
                        "Code": "private",
                    }
                ],
            }
        ]
        report = module.summarize(raw, PROOF, DB)
        self.assertEqual(report["secret_observations"][0]["rule_id"], "private-key")
        self.assertEqual(
            report["secret_observations"][0]["location"],
            "python_stdlib_test_certdata",
        )
        self.assertNotIn("sensitive-test-value", json.dumps(report))
        self.assertEqual(report["gate"], "failed")
        raw["Results"][0]["Target"] = "untrusted-value"
        self.assertEqual(
            module.summarize(raw, PROOF, DB)["secret_observations"][0]["location"],
            "withheld",
        )

    def test_secret_looking_filenames_never_enter_evidence(self):
        location = "/app/synthetic-credential-value.pem"
        self.assertEqual(module.public_image_location(location), "application_file")
        self.assertNotIn(
            "synthetic-credential-value", module.public_image_location(location)
        )

    def test_jwt_triage_does_not_promote_arbitrary_tokens_or_retain_claims(self):
        result = module.jwt_triage("not-a-token")
        self.assertEqual(result["classification"], "analysis_required")
        self.assertNotIn("not-a-token", json.dumps(result))

    def test_public_jwt_example_requires_demo_signature_not_claims_alone(self):
        def encode(value):
            return module.base64.urlsafe_b64encode(value).decode().rstrip("=")

        header = encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())
        payload = encode(
            json.dumps(
                {"sub": "1234567890", "name": "John Doe", "iat": 1516239022}
            ).encode()
        )
        unsigned = header + "." + payload
        signature = encode(
            module.hmac.new(
                b"your-256-bit-secret", unsigned.encode(), module.hashlib.sha256
            ).digest()
        )
        report = module.jwt_triage(unsigned + "." + signature)
        self.assertEqual(report["classification"], "public_documentation_example")
        self.assertNotIn(signature, json.dumps(report))
        self.assertEqual(
            module.jwt_triage(unsigned + "." + encode(b"different"))["classification"],
            "analysis_required",
        )

    def test_omitted_results_is_valid_clean_report(self):
        self.assertEqual(
            module.summarize(fixture(), PROOF, DB)["execution"], "completed_clean"
        )

    def test_malformed_reports_fail_closed(self):
        candidates = [
            {},
            [],
            {**fixture(), "Results": {}},
            {**fixture(), "Results": [None]},
            {**fixture(), "Results": [{"Secrets": None}]},
            {**fixture(), "Metadata": {}},
            {
                **fixture(),
                "Results": [
                    {"Vulnerabilities": [{"VulnerabilityID": "private-value"}]}
                ],
            },
        ]
        for raw in candidates:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                module.summarize(raw, PROOF, DB)
        for database in ({}, None):
            with self.assertRaises(ValueError):
                module.summarize(fixture(), PROOF, database)
        raw = fixture()
        raw["Metadata"]["ImageConfig"]["architecture"] = "amd64"
        with self.assertRaises(ValueError):
            module.summarize(raw, PROOF, DB)
        raw = fixture()
        raw["Metadata"].pop("OS")
        with self.assertRaises(ValueError):
            module.summarize(raw, PROOF, DB)
