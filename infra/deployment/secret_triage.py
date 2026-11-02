"""Read verified OCI file contents only in RAM; return categorical secret facts.

This supplements scanner findings and never changes the release gate. Links and
ambiguous overlay entries deliberately remain unclassified.
"""

import hashlib
import json
from pathlib import PurePosixPath
import re
import tarfile

MAX_MEMBERS = 20_000
MAX_EXPANDED_BYTES = 4 * 1024**3
MAX_FILE_BYTES = 16 * 1024**2
JWT = re.compile(rb"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]*")


def _name(value):
    if not isinstance(value, str) or "\x00" in value:
        raise ValueError("unresolved")
    value = value.removeprefix("/")
    while value.startswith("./"):
        value = value[2:]
    path = PurePosixPath(value)
    if not value or path.is_absolute() or ".." in path.parts:
        raise ValueError("unresolved")
    return str(path)


def _blob(layout, descriptor, limit=None):
    digest = descriptor.get("digest", "")
    if not re.fullmatch(r"sha256:[a-f0-9]{64}", digest):
        raise ValueError("unresolved")
    path = layout / "blobs" / "sha256" / digest[7:]
    if path.is_symlink() or path.stat().st_size != descriptor.get("size"):
        raise ValueError("unresolved")
    if limit is not None and path.stat().st_size > limit:
        raise ValueError("unresolved")
    checksum = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(chunk)
    if checksum.hexdigest() != digest[7:]:
        raise ValueError("unresolved")
    return path


def _contents(layout, proof, target):
    if proof.get("status") != "verified":
        raise ValueError("unresolved")
    manifest = json.loads(
        _blob(layout, proof["descriptor"], MAX_FILE_BYTES).read_bytes()
    )
    target = _name(target)
    parts = target.split("/")
    ancestors = ["/".join(parts[:i]) for i in range(1, len(parts))]
    hidden = {"/".join(parts[:i] + [".wh." + parts[i]]) for i in range(len(parts))}
    opaque = {".wh..wh..opq"} | {p + "/.wh..wh..opq" for p in ancestors}
    count = expanded = 0
    for descriptor in reversed(manifest["layers"]):
        found = None
        blocked = False
        seen = set()
        with tarfile.open(_blob(layout, descriptor), mode="r|*") as layer:
            for member in layer:
                count += 1
                expanded += max(member.size, 0)
                if count > MAX_MEMBERS or expanded > MAX_EXPANDED_BYTES:
                    raise ValueError("unresolved")
                name = _name(member.name)
                relevant = (
                    name == target or name in ancestors or name in hidden | opaque
                )
                if relevant and name in seen:
                    raise ValueError("unresolved")
                if relevant:
                    seen.add(name)
                if name in ancestors and not member.isdir():
                    raise ValueError("unresolved")
                if name in hidden | opaque:
                    blocked = True
                if name == target:
                    if not member.isfile() or member.size > MAX_FILE_BYTES:
                        raise ValueError("unresolved")
                    found = layer.extractfile(member).read(MAX_FILE_BYTES + 1)
                    if len(found) != member.size:
                        raise ValueError("unresolved")
        if found is not None:
            # Reject even unusual same-layer whiteout/replacement combinations.
            if blocked:
                raise ValueError("unresolved")
            return found
        if blocked:
            raise ValueError("unresolved")
    raise ValueError("unresolved")


def triage_secrets(layout, proof, raw, classifier):
    """One fixed-shape result per original alert, in original order.

    The trusted callback must itself emit only fixed categories and booleans.
    Scanner Match/Code are censored upstream and are never used as evidence.
    """
    observations = []
    for result in raw.get("Results", []):
        target = result.get("Target", "")
        for secret in result.get("Secrets", []):
            item = {
                "classification": "analysis_required",
                "value_retained": False,
                "is_pip_download_cache": False,
                "is_conda_package_cache": False,
                "forensic_status": "unresolved",
            }
            try:
                name = _name(target)
                item["is_pip_download_cache"] = name.startswith("root/.cache/pip/")
                item["is_conda_package_cache"] = name.startswith("opt/conda/pkgs/")
                if secret.get("RuleID") != "jwt-token":
                    observations.append(item)
                    continue
                item["forensic_stage"] = "offset_validation"
                offset = secret.get("Offset", 0)
                if type(offset) is not int or offset < 0:
                    raise ValueError("unresolved")
                item["forensic_stage"] = "verified_file_resolution"
                content = _contents(layout, proof, name)
                # Exact byte offset only: never classify a nearby unrelated token.
                item["forensic_stage"] = "exact_offset_match"
                match = JWT.match(content, offset)
                if match is None or match.end() - offset > 16384:
                    raise ValueError("unresolved")
                item["forensic_stage"] = "token_classification"
                item.update(classifier(match.group().decode("ascii")))
                item["forensic_status"] = "resolved_in_memory"
            except Exception:
                # Never expose exception text, paths, offsets or file contents.
                pass
            observations.append(item)
    return observations
