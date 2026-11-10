"""Export installed closures, then freeze exact PyPI release hashes separately.

Export runs inside the baseline environment (requires packaging). Generation runs
outside containers and never selects versions, resolves upgrades or installs code.
"""

import argparse
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import sys
import urllib.request

BASELINE = "9ebbf2cd993395af2b154efb0b4cf5a76b4dd079"


def export_closure(root):
    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name

    needed = {canonicalize_name(root): set()}
    processed = {}
    while any(
        name not in processed or processed[name] != extras
        for name, extras in needed.items()
    ):
        for name, extras in list(needed.items()):
            if name in processed and processed[name] == extras:
                continue
            processed[name] = set(extras)
            for text in metadata.distribution(name).requires or []:
                requirement = Requirement(text)
                if requirement.marker and not any(
                    requirement.marker.evaluate({"extra": extra})
                    for extra in extras | {""}
                ):
                    continue
                child = canonicalize_name(requirement.name)
                # Installed metadata must actually satisfy its declaring parent.
                if requirement.specifier and not requirement.specifier.contains(
                    metadata.version(child)
                ):
                    raise ValueError("installed_dependency_outside_requirement")
                needed.setdefault(child, set()).update(requirement.extras)
    return {
        "root": root,
        "root_version": metadata.version(root),
        "python": sys.version.split()[0],
        "packages": [
            {"name": name, "version": metadata.version(name), "extras": sorted(extras)}
            for name, extras in sorted(needed.items())
            if name != canonicalize_name(root)
        ],
    }


def graph_packages(graph, include_root=False, root_version=None):
    packages = [dict(p) for p in graph["packages"]]
    if include_root:
        version = graph.get("root_version") or root_version
        if not version:
            raise ValueError("explicit_build_root_version_required")
        if root_version and graph.get("root_version", root_version) != root_version:
            raise ValueError("build_root_version_mismatch")
        packages.append({"name": graph["root"], "version": version, "extras": []})
    seen = set()
    for package in packages:
        name, version = package["name"], package["version"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or not re.fullmatch(
            r"[A-Za-z0-9.+!-]+", version
        ):
            raise ValueError("invalid_package_identity")
        if (
            name in seen
            or not isinstance(package.get("extras"), list)
            or any(
                not re.fullmatch(r"[a-z0-9._-]+", extra) for extra in package["extras"]
            )
        ):
            raise ValueError("invalid_package_graph")
        if name == "kombu" and version != "5.6.2":
            raise ValueError("kombu_pin_must_remain_5_6_2")
        seen.add(name)
    return sorted(packages, key=lambda p: p["name"])


def release_url(name, version):
    graph_packages({"packages": [{"name": name, "version": version, "extras": []}]})
    return f"https://pypi.org/pypi/{name}/{version}/json"


def validate_release(name, version, release):
    if release.get("url") != release_url(name, version):
        raise ValueError("release_url_mismatch")
    if not release.get("hashes") or any(
        not re.fullmatch(r"[a-f0-9]{64}", digest) for digest in release["hashes"]
    ):
        raise ValueError("invalid_release_hashes")
    if not re.fullmatch(r"[a-f0-9]{64}", release.get("metadata_sha256", "")):
        raise ValueError("invalid_metadata_hash")


def fetch_release(name, version):
    url = release_url(name, version)
    with urllib.request.urlopen(url, timeout=60) as response:
        if response.url != url:
            raise ValueError("release_redirect_refused")
        payload = response.read(16 * 1024 * 1024 + 1)
    if len(payload) > 16 * 1024 * 1024:
        raise ValueError("release_metadata_too_large")
    public = json.loads(payload)
    if public["info"]["version"] != version:
        raise ValueError("release_version_mismatch")
    release = {
        "url": url,
        "hashes": sorted({item["digests"]["sha256"] for item in public["urls"]}),
        "metadata_sha256": hashlib.sha256(payload).hexdigest(),
    }
    validate_release(name, version, release)
    return release


def generate(graph_paths, output, build_root_version, release_provenance=None):
    if output.exists() and any(output.iterdir()):
        raise ValueError("output_must_be_empty_no_lock_overwrite")
    graphs = {
        role: graph_packages(
            json.loads(path.read_text()),
            include_root=role == "build",
            root_version=build_root_version if role == "build" else None,
        )
        for role, path in graph_paths.items()
    }
    pairs = sorted(
        {(p["name"], p["version"]) for packages in graphs.values() for p in packages}
    )
    if release_provenance is None:
        releases = {
            (name, version): fetch_release(name, version) for name, version in pairs
        }
    else:
        retained = json.loads(release_provenance.read_text())["release_metadata"]
        releases = {}
        for name, version in pairs:
            release = retained[name + "==" + version]
            validate_release(name, version, release)
            releases[(name, version)] = release
    output.mkdir(parents=True, exist_ok=True)
    for role, packages in graphs.items():
        graph_metadata = json.loads(graph_paths[role].read_text())
        lines = [
            (
                "# Derived from main9ebbf2c closure with explicit targeted security updates; PyPI release SHA256s."
                if graph_metadata.get("derivation")
                else "# Frozen from main9ebbf2c installed runtime dependency closure; PyPI release SHA256s."
            ),
            "# No global dependency update; kombu==5.6.2 retained.",
        ]
        for package in packages:
            extras = (
                "[" + ",".join(package["extras"]) + "]" if package["extras"] else ""
            )
            lines.append(package["name"] + extras + "==" + package["version"] + " \\")
            hashes = releases[(package["name"], package["version"])]["hashes"]
            lines.extend(
                "    --hash=sha256:" + digest + (" \\" if i < len(hashes) - 1 else "")
                for i, digest in enumerate(hashes)
            )
        (output / (role + ".txt")).write_text("\n".join(lines) + "\n")
    provenance = {
        "baseline_source": BASELINE,
        "source": "https://pypi.org/pypi/{name}/{version}/json",
        "input_graphs": {
            role: {"sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            for role, path in graph_paths.items()
        },
        "release_metadata": {
            name + "==" + version: release
            for (name, version), release in sorted(releases.items())
        },
        "derived_graphs": {
            role: json.loads(path.read_text())["derivation"]
            for role, path in graph_paths.items()
            if "derivation" in json.loads(path.read_text())
        },
    }
    (output / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    export.add_argument("--root", required=True)
    export.add_argument("--output", type=Path, required=True)
    freeze = sub.add_parser("generate")
    for role in ("api", "worker", "build"):
        freeze.add_argument("--" + role + "-graph", type=Path, required=True)
    freeze.add_argument("--build-root-version", required=True)
    freeze.add_argument(
        "--release-provenance",
        type=Path,
        help="Replay retained exact release hashes offline instead of querying PyPI",
    )
    freeze.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "export":
        args.output.write_text(
            json.dumps(export_closure(args.root), indent=2, sort_keys=True) + "\n"
        )
    else:
        generate(
            {
                role: getattr(args, role + "_graph")
                for role in ("api", "worker", "build")
            },
            args.output,
            args.build_root_version,
            args.release_provenance,
        )


if __name__ == "__main__":
    main()
