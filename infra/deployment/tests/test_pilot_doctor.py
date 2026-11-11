from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from doctor import (
    certificate_checks,
    protected_file,
    mandatory_blockers,
    namespace_checks,
)


class PilotDoctorTests(unittest.TestCase):
    def test_open_gates_are_not_caller_overridable(self):
        self.assertEqual(mandatory_blockers(), ["AUTH_B6", "OWNER_PILOT_AUTHORIZATION"])

    def test_protected_input_rejects_symlink_and_group_write(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            p = root / "private"
            p.write_text("synthetic")
            p.chmod(0o600)
            self.assertTrue(protected_file(p, secret=True))
            p.chmod(0o660)
            self.assertFalse(protected_file(p, secret=True))
            p.chmod(0o600)
            link = root / "link"
            link.symlink_to(p)
            self.assertFalse(protected_file(link, secret=True))

    def test_real_temporary_certificate_name_and_key_checks(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            key = root / "key.pem"
            cert = root / "cert.pem"
            subprocess.run(
                [
                    "openssl",
                    "req",
                    "-x509",
                    "-newkey",
                    "rsa:2048",
                    "-nodes",
                    "-days",
                    "2",
                    "-subj",
                    "/CN=pilot.test",
                    "-addext",
                    "subjectAltName=DNS:pilot.test",
                    "-addext",
                    "basicConstraints=critical,CA:TRUE",
                    "-keyout",
                    str(key),
                    "-out",
                    str(cert),
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            key.chmod(0o600)
            self.assertEqual(
                certificate_checks(cert, key, cert, "pilot.test")[
                    "tls_chain_name_expiry_key"
                ],
                "PASS",
            )
            self.assertEqual(
                certificate_checks(cert, key, cert, "wrong.test")[
                    "tls_chain_name_expiry_key"
                ],
                "FAIL",
            )
            wrong = root / "wrong.pem"
            subprocess.run(
                [
                    "openssl",
                    "genpkey",
                    "-algorithm",
                    "RSA",
                    "-out",
                    str(wrong),
                    "-pkeyopt",
                    "rsa_keygen_bits:2048",
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            wrong.chmod(0o600)
            self.assertEqual(
                certificate_checks(cert, wrong, cert, "pilot.test")[
                    "tls_chain_name_expiry_key"
                ],
                "FAIL",
            )

    def test_existing_target_is_blocked_without_reading_volume_data(self):
        from unittest.mock import patch

        with patch(
            "doctor.command",
            side_effect=[b"oligospace-pilot_postgres_data", b"", b"", b""],
        ) as run:
            checks = namespace_checks(["docker"], {}, "oligospace-pilot")
        self.assertEqual(checks["target_namespace"], "BLOCKED")
        self.assertEqual(checks["ingress_port"], "NOT_VERIFIED")
        self.assertFalse(any("inspect" in call.args[0] for call in run.call_args_list))

    def test_public_configuration_cannot_be_modified_by_other_users(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "config"
            p.write_text("synthetic")
            for mode in (0o666, 0o664, 0o660):
                p.chmod(mode)
                self.assertFalse(protected_file(p))
            p.chmod(0o644)
            self.assertTrue(protected_file(p))
