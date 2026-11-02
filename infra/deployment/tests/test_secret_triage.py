import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import secret_triage as scanner


def token():
    return b".".join(
        base64.urlsafe_b64encode(value).rstrip(b"=")
        for value in (b'{"alg":"HS256"}', b'{"synthetic":true}', bytes(range(32)))
    )


def layout(root, layers):
    def blob(data):
        digest = hashlib.sha256(data).hexdigest()
        path = root / "blobs" / "sha256" / digest
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return {"digest": "sha256:" + digest, "size": len(data)}

    descriptors = []
    for entries in layers:
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w") as archive:
            for name, value in entries:
                member = tarfile.TarInfo(name)
                if value is None:
                    member.type = tarfile.SYMTYPE
                    member.linkname = "/elsewhere"
                    archive.addfile(member)
                else:
                    member.size = len(value)
                    archive.addfile(member, io.BytesIO(value))
        descriptors.append(blob(output.getvalue()))
    return {
        "status": "verified",
        "descriptor": blob(json.dumps({"layers": descriptors}).encode()),
    }


class SecretTriageTests(unittest.TestCase):
    def inspect(self, layers, offset=3, target="root/.cache/pip/test"):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proof = layout(root, layers)
            calls = []

            def classify(value):
                calls.append(value)
                return {"classification": "synthetic_verified", "value_retained": False}

            raw = {
                "Results": [
                    {
                        "Target": target,
                        "Secrets": [
                            {"RuleID": "jwt-token", "Offset": offset, "Match": "***"},
                            {"RuleID": "other", "Offset": offset},
                        ],
                    }
                ]
            }
            report = scanner.triage_secrets(root, proof, raw, classify)
            self.assertEqual(len(report), 2)
            self.assertNotIn(token().decode(), json.dumps(report))
            return report, calls

    def test_exact_offset_and_all_alerts_preserved(self):
        report, calls = self.inspect([[("root/.cache/pip/test", b"x: " + token())]])
        self.assertEqual(len(calls), 1)
        self.assertEqual(report[0]["classification"], "synthetic_verified")
        self.assertTrue(report[0]["is_pip_download_cache"])
        self.assertEqual(report[1]["classification"], "analysis_required")

    def test_whiteouts_opaque_and_links_do_not_recover_hidden_token(self):
        original = [("root/.cache/pip/test", b"x: " + token())]
        for entry in [
            ("root/.cache/pip/.wh.test", b""),
            ("root/.cache/.wh.pip", b""),
            ("root/.cache/pip/.wh..wh..opq", b""),
            ("root/.cache/pip", None),
            ("root/.cache/pip/test", None),
        ]:
            with self.subTest(kind=entry[0]):
                report, calls = self.inspect([original, [entry]])
                self.assertFalse(calls)
                self.assertEqual(report[0]["forensic_status"], "unresolved")

    def test_bounds_and_incorrect_offsets_fail_closed(self):
        entries = [[("root/.cache/pip/test", b"x: " + token())]]
        for name in ("MAX_MEMBERS", "MAX_EXPANDED_BYTES", "MAX_FILE_BYTES"):
            with patch.object(scanner, name, 0):
                report, calls = self.inspect(entries)
                self.assertFalse(calls)
                self.assertEqual(report[0]["forensic_status"], "unresolved")
        for offset in (-1, True, 0, 99999):
            report, calls = self.inspect(entries, offset=offset)
            self.assertFalse(calls)

    def test_newest_regular_file_and_invalid_paths(self):
        report, calls = self.inspect(
            [
                [("root/.cache/pip/test", b"old")],
                [("root/.cache/pip/test", b"x: " + token())],
            ]
        )
        self.assertEqual(len(calls), 1)
        report, calls = self.inspect([], target="../escape")
        self.assertFalse(calls)

    def test_unverified_or_modified_blobs_are_never_classified(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proof = layout(root, [[("target", token())]])
            raw = {
                "Results": [
                    {
                        "Target": "target",
                        "Secrets": [{"RuleID": "jwt-token", "Offset": 0}],
                    }
                ]
            }
            calls = []

            def callback(value):
                calls.append(value)
                return {}

            invalid = {**proof, "status": "unverified"}
            self.assertEqual(
                scanner.triage_secrets(root, invalid, raw, callback)[0][
                    "forensic_status"
                ],
                "unresolved",
            )
            manifest_path = (
                root / "blobs" / "sha256" / proof["descriptor"]["digest"][7:]
            )
            manifest = json.loads(manifest_path.read_bytes())
            path = root / "blobs" / "sha256" / manifest["layers"][0]["digest"][7:]
            data = bytearray(path.read_bytes())
            data[-1] ^= 1
            path.write_bytes(data)
            self.assertEqual(
                scanner.triage_secrets(root, proof, raw, callback)[0][
                    "forensic_status"
                ],
                "unresolved",
            )
            self.assertFalse(calls)


if __name__ == "__main__":
    unittest.main()
