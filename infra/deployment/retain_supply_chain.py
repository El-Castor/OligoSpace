"""Retain minimal, explicitly unsigned projections of verified OCI attestations."""

import hashlib
import json
from pathlib import Path
import re
import tarfile

from oci import verify_oci
from scan_artifact import safe_field

SPDX = "https://spdx.dev/Document"
PROVENANCE = {
    "https://slsa.dev/provenance/v0.2",
    "https://slsa.dev/provenance/v1",
}
BUILD_TYPES = {"https://mobyproject.org/buildkit@v1"}


def package_projection(package):
    retained = {}
    for key in ("name", "versionInfo", "SPDXID", "licenseConcluded", "licenseDeclared"):
        if key not in package:
            continue
        value = safe_field(package[key])
        if "://" in value or (
            key == "SPDXID" and not re.fullmatch(r"SPDXRef-[A-Za-z0-9.-]+", value)
        ):
            raise ValueError("invalid_spdx_package_field")
        retained[key] = value
    if not retained.get("name") or not retained.get("SPDXID"):
        raise ValueError("invalid_spdx_package")
    return retained


def retain_supply_chain(archive, proof, outputdir):
    """Return filenames after rechecking proof identity and all reachable bytes.

    The projections omit files, URLs, free text, invocation and environment.
    Their original attestation digests identify the original OCI blob, not the
    derived projection. Presence and hash integrity confer no signature trust.
    """
    if proof.get("status") != "verified":
        raise ValueError("verified_oci_proof_required")
    verified = verify_oci(Path(archive), proof["architecture"], proof["source"])
    if any(
        proof.get(key) != verified[key]
        for key in ("descriptor", "config_digest", "source", "architecture")
    ):
        raise ValueError("proof_identity_mismatch")
    subject_digest = proof["descriptor"]["digest"]
    common = {
        "sanitized_projection": True,
        "original_verbatim": False,
        "signature_trust": "not_verified",
        "subject_digest": subject_digest,
        "source_sha": proof["source"],
        "source_sha_authority": "verified_image_revision_label",
        "architecture": proof["architecture"],
    }
    sboms, provenance = [], []
    with tarfile.open(archive) as tar:
        members = {
            member.name.removeprefix("./"): member for member in tar.getmembers()
        }

        def blob(descriptor):
            digest = descriptor["digest"]
            if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
                raise ValueError("invalid_digest")
            member = members["blobs/sha256/" + digest[7:]]
            if not member.isfile() or member.size > 32 * 1024 * 1024:
                raise ValueError("invalid_attestation_document")
            data = tar.extractfile(member).read()
            if (
                len(data) != descriptor["size"]
                or "sha256:" + hashlib.sha256(data).hexdigest() != digest
            ):
                raise ValueError("blob_digest_mismatch")
            return json.loads(data)

        def visit(descriptor):
            document = blob(descriptor)
            if "manifests" in document:
                for child in document["manifests"]:
                    visit(child)
                return
            for layer in document.get("layers", []):
                if layer.get("mediaType") != "application/vnd.in-toto+json":
                    continue
                statement = blob(layer)
                kind = statement.get("predicateType")
                if kind != SPDX and kind not in PROVENANCE:
                    continue
                subjects = statement.get("subject", [])
                if not subjects or any(
                    subject.get("digest", {}).get("sha256") != subject_digest[7:]
                    for subject in subjects
                ):
                    raise ValueError("attestation_subject_mismatch")
                retained = {
                    **common,
                    "predicateType": kind,
                    "original_attestation_blob_digest": layer["digest"],
                }
                predicate = statement["predicate"]
                if kind == SPDX:
                    if predicate.get("spdxVersion") != "SPDX-2.3" or not isinstance(
                        predicate.get("packages"), list
                    ):
                        raise ValueError("spdx_23_package_inventory_required")
                    retained["spdxVersion"] = "SPDX-2.3"
                    retained["packages"] = [
                        package_projection(package) for package in predicate["packages"]
                    ]
                    sboms.append(retained)
                else:
                    build_type = predicate.get(
                        "buildType",
                        predicate.get("buildDefinition", {}).get("buildType"),
                    )
                    retained["build_type"] = (
                        build_type
                        if build_type in BUILD_TYPES
                        else "withheld_or_unknown"
                    )
                    provenance.append(retained)

        index = json.load(tar.extractfile(members["index.json"]))
        for descriptor in index["manifests"]:
            visit(descriptor)
    if not sboms or not provenance:
        raise ValueError("bound_sbom_and_provenance_required")
    outputdir = Path(outputdir)
    filenames = ("sbom-projection.json", "provenance-projection.json")
    if outputdir.is_symlink() or any(
        (outputdir / name).is_symlink() for name in filenames
    ):
        raise ValueError("projection_symlink_refused")
    outputdir.mkdir(parents=True, exist_ok=True)
    for filename, documents in zip(filenames, (sboms, provenance)):
        (outputdir / filename).write_text(
            json.dumps({**common, "attestations": documents}, indent=2) + "\n"
        )
    return {
        **common,
        "sbom": filenames[0],
        "provenance": filenames[1],
        "sbom_attestations": len(sboms),
        "provenance_attestations": len(provenance),
    }
