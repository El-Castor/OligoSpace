import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from oci import verify_oci
from retain_supply_chain import package_projection, retain_supply_chain
from test_oci import archive


def rewrite(path, transform):
    with tarfile.open(path) as tar:
        files = {
            member.name: tar.extractfile(member).read() for member in tar.getmembers()
        }
    transform(files)
    with tarfile.open(path, "w") as tar:
        for name, data in files.items():
            member = tarfile.TarInfo(name)
            member.size = len(data)
            tar.addfile(member, io.BytesIO(data))


class RetentionTests(unittest.TestCase):
    def test_package_projection_rejects_urls_even_in_retained_fields(self):
        with self.assertRaises(ValueError):
            package_projection(
                {"name": "https://private.invalid", "SPDXID": "SPDXRef-test"}
            )

    def test_changed_blob_and_wrong_proof_subject_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "image.tar"
            archive(image)
            proof = verify_oci(image, "arm64", "a" * 40)
            wrong = {
                **proof,
                "descriptor": {**proof["descriptor"], "digest": "sha256:" + "0" * 64},
            }
            with self.assertRaises(ValueError):
                retain_supply_chain(image, wrong, root / "wrong")

            def corrupt(files):
                name = next(
                    name for name, data in files.items() if b'"predicateType"' in data
                )
                files[name] += b"changed"

            rewrite(image, corrupt)
            with self.assertRaises(ValueError):
                retain_supply_chain(image, proof, root / "changed")
            self.assertFalse((root / "changed").exists())

    def test_projection_retains_only_subject_bound_public_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            image = root / "image.tar"
            archive(image)

            def enrich(files):
                replacements = {}
                for name, data in list(files.items()):
                    if b'"predicateType"' not in data:
                        continue
                    document = json.loads(data)
                    if document["predicateType"] == "https://spdx.dev/Document":
                        document["predicate"] = {
                            "spdxVersion": "SPDX-2.3",
                            "packages": [
                                {
                                    "name": "openssl",
                                    "versionInfo": "3.0.1",
                                    "SPDXID": "SPDXRef-openssl",
                                    "licenseDeclared": "Apache-2.0",
                                    "licenseConcluded": "NOASSERTION",
                                    "downloadLocation": "private-secret",
                                    "annotations": ["private-secret"],
                                }
                            ],
                            "files": [{"fileName": "private-secret"}],
                        }
                    else:
                        document["predicate"] = {
                            "buildType": "https://mobyproject.org/buildkit@v1",
                            "invocation": {"environment": {"TOKEN": "private-secret"}},
                        }
                    updated = json.dumps(document).encode()
                    new_digest = hashlib.sha256(updated).hexdigest()
                    replacements[name.rsplit("/", 1)[1]] = (new_digest, len(updated))
                    del files[name]
                    files["blobs/sha256/" + new_digest] = updated
                # Update reachable manifests and their descriptors transitively.
                while replacements:
                    current, replacements = replacements, {}
                    for name, data in list(files.items()):
                        if not any(old.encode() in data for old in current):
                            continue
                        document = json.loads(data)

                        def update(value):
                            if isinstance(value, dict):
                                for old, (new, size) in current.items():
                                    if value.get("digest") == "sha256:" + old:
                                        value.update(digest="sha256:" + new, size=size)
                                for child in value.values():
                                    update(child)
                            elif isinstance(value, list):
                                for child in value:
                                    update(child)

                        update(document)
                        updated = json.dumps(document).encode()
                        if name == "index.json":
                            files[name] = updated
                        else:
                            new = hashlib.sha256(updated).hexdigest()
                            replacements[name.rsplit("/", 1)[1]] = (new, len(updated))
                            del files[name]
                            files["blobs/sha256/" + new] = updated

            rewrite(image, enrich)
            proof = verify_oci(image, "arm64", "a" * 40)
            result = retain_supply_chain(image, proof, root / "retained")
            output = "".join(
                path.read_text() for path in (root / "retained").glob("*.json")
            )
            self.assertNotIn("private-secret", output)
            self.assertIn("openssl", output)
            self.assertIn("Apache-2.0", output)
            self.assertEqual(result["signature_trust"], "not_verified")
            self.assertTrue(result["sanitized_projection"])
