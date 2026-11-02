"""Observe selected Debian package files in an isolated, identity-checked image.

Point-in-time presence and selected loader observations do not prove reachable
vulnerable code, complete runtime dependencies, or absence of vulnerabilities.
No package deletion, environment collection, or configuration-file reads.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import posixpath
import json
import os
from pathlib import Path
import re
import subprocess

PACKAGES = (
    "bsdutils",
    "libblkid1",
    "liblastlog2-2",
    "libmount1",
    "libsmartcols1",
    "libuuid1",
    "login",
    "mount",
    "util-linux",
    "libacl1",
    "libsqlite3-0",
    "libsystemd0",
    "libudev1",
    "libtinfo6",
    "ncurses-base",
    "ncurses-bin",
    "perl-base",
)
EXECUTABLES = (
    "/opt/conda/bin/python",
    "/opt/primer3/bin/primer3_core",
    "/opt/primer3/bin/oligotm",
    "/opt/primer3/bin/ntthal",
)
DIGEST = r"sha256:[0-9a-f]{64}"
PUBLIC_PATH = r"/(?:usr/)?(?:lib|lib64|bin|sbin)/[A-Za-z0-9_./+:-]+|/opt/(?:conda|ncbi-blast|primer3)/[A-Za-z0-9_./+:-]+"


def command(argv):
    result = subprocess.run(
        argv, capture_output=True, text=True, timeout=90, check=False
    )
    if len(result.stdout) > 2 * 1024 * 1024:
        raise ValueError("output_limit")
    return result.returncode, result.stdout


def parse_metadata(text, package):
    rows = [row.split("\t") for row in text.splitlines()]
    if len(rows) != 1 or len(rows[0]) != 5:
        return {"package": package, "observation": "package_metadata_unavailable"}
    binary, version, source, source_version, status = rows[0]
    if (
        binary.split(":")[0] != package
        or not all(
            re.fullmatch(r"[A-Za-z0-9.+:~_-]+", value)
            for value in (binary, version, source, source_version)
        )
        or status not in ("install ok installed", "deinstall ok config-files")
    ):
        return {"package": package, "observation": "package_metadata_unavailable"}
    return {
        "package": package,
        "binary_version": version,
        "source_package": source,
        "source_version": source_version,
        "dpkg_status": status,
        "observation": "installed"
        if status == "install ok installed"
        else "not_installed",
    }


def file_presence(paths):
    counts = {
        "listed_paths": len(paths),
        "existing_regular_files": 0,
        "existing_symlinks": 0,
        "missing_paths": 0,
        "other_paths": 0,
    }
    for name in paths:
        path = Path(name)
        if not path.is_absolute() or ".." in path.parts:
            raise ValueError("invalid_package_path")
        if path.is_symlink():
            counts["existing_symlinks"] += 1
        elif path.is_file():
            counts["existing_regular_files"] += 1
        elif not path.exists():
            counts["missing_paths"] += 1
        else:
            counts["other_paths"] += 1
    return counts


def parse_ldd(text):
    rows = []
    for line in text.splitlines()[:256]:
        match = re.fullmatch(
            r"\s*([A-Za-z0-9_.+-]+) => (" + PUBLIC_PATH + r") \(0x[0-9a-f]+\)\s*", line
        )
        if not match:
            continue
        path = posixpath.normpath(match[2])
        if not re.fullmatch(PUBLIC_PATH, path):
            continue
        origin = (
            "conda"
            if path.startswith("/opt/conda/")
            else (
                "blast"
                if path.startswith("/opt/ncbi-blast/")
                else (
                    "primer3" if path.startswith("/opt/primer3/") else "debian_system"
                )
            )
        )
        rows.append({"soname": match[1], "path": path, "origin": origin})
    return rows


def representative(paths):
    for name in sorted(paths):
        if not re.fullmatch(PUBLIC_PATH, name) or ".." in Path(name).parts:
            continue
        path = Path(name)
        # Resolve before reading so a package symlink cannot redirect to config.
        resolved = str(path.resolve())
        if not re.fullmatch(PUBLIC_PATH, resolved) or not path.is_file():
            continue
        if path.stat().st_size > 64 * 1024 * 1024:
            continue
        with path.open("rb") as stream:
            header = stream.read(4)
            if header != b"\x7fELF":
                continue
            digest = hashlib.sha256(header)
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return {"path": name, "sha256": digest.hexdigest(), "kind": "ELF"}
    return None


def probe():
    packages = []
    for package in PACKAGES:
        code, text = command(
            [
                "/usr/bin/dpkg-query",
                "-W",
                "-f=${binary:Package}\t${Version}\t${source:Package}\t${source:Version}\t${Status}\n",
                package,
            ]
        )
        row = parse_metadata(text if code == 0 else "", package)
        if row["observation"] == "installed":
            code, text = command(["/usr/bin/dpkg-query", "-L", package])
            if code == 0:
                paths = text.splitlines()
                if len(paths) > 20000:
                    raise ValueError("package_path_limit")
                row["files"] = file_presence(paths)
                row["representative_public_elf"] = representative(paths)
            else:
                row["file_observation"] = "listing_unavailable"
        packages.append(row)
    loaders = []
    selected = list(EXECUTABLES)
    for module in ("_sqlite3", "readline"):
        spec = importlib.util.find_spec(module)
        if spec and spec.origin and spec.origin.startswith("/opt/conda/"):
            selected.append(spec.origin)
    for name in selected:
        path = Path(name)
        if not path.is_file():
            loaders.append({"executable": name, "observation": "absent"})
            continue
        if not str(path.resolve()).startswith(("/opt/conda/", "/opt/primer3/")):
            raise ValueError("executable_root_mismatch")
        code, text = command(["/usr/bin/ldd", name])
        loaders.append(
            {
                "executable": name,
                "observation": "loader_reported" if code == 0 else "loader_unavailable",
                "libraries": parse_ldd(text) if code == 0 else [],
            }
        )
    return {
        "packages": packages,
        "selected_loader_observations": loaders,
        "metadata_coverage": "complete"
        if all(row["observation"] == "installed" for row in packages)
        else "incomplete",
        "file_and_loader_coverage": "selected_observations_only",
    }


def image_matches(loaded, proof):
    return (
        proof.get("status") == "verified"
        and re.fullmatch(r"[0-9a-f]{40}", proof.get("source", "")) is not None
        and re.fullmatch(DIGEST, proof.get("config_digest", "")) is not None
        and bool(proof.get("rootfs_diff_ids"))
        and all(re.fullmatch(DIGEST, item) for item in proof["rootfs_diff_ids"])
        and loaded.get("Id") == proof["config_digest"]
        and loaded.get("Architecture") == proof.get("architecture")
        and loaded.get("Os") == "linux"
        and loaded.get("RootFS", {}).get("Layers") == proof["rootfs_diff_ids"]
        and loaded.get("Config", {})
        .get("Labels", {})
        .get("org.opencontainers.image.revision")
        == proof["source"]
        and loaded.get("Config", {}).get("User", "").split(":")[0]
        not in ("", "0", "root")
    )


def host(context, proof):
    if any(os.environ.get(key) for key in ("DOCKER_HOST", "DOCKER_CONTEXT")):
        raise ValueError("docker_override_refused")
    docker = ["docker", "--context", context]

    def output(args):
        code, text = command(docker + args)
        if code:
            raise ValueError("docker_command_failed")
        return text

    endpoint = json.loads(output(["context", "inspect", context]))[0]["Endpoints"][
        "docker"
    ]["Host"]
    if not endpoint.startswith("unix://"):
        raise ValueError("local_context_required")
    loaded = json.loads(output(["image", "inspect", proof["config_digest"]]))[0]
    if not image_matches(loaded, proof):
        raise ValueError("image_proof_mismatch")
    native = {
        "x86_64": "amd64",
        "amd64": "amd64",
        "aarch64": "arm64",
        "arm64": "arm64",
    }.get(output(["info", "--format", "{{.Architecture}}"]).strip())
    if native != proof["architecture"]:
        raise ValueError("native_platform_required")
    script = str(Path(__file__).resolve())
    observation = json.loads(
        output(
            [
                "run",
                "--rm",
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--tmpfs",
                "/tmp:size=64m",
                "--mount",
                "type=bind,src=" + script + ",dst=/inspection.py,readonly",
                "--entrypoint",
                "/bin/micromamba",
                proof["config_digest"],
                "run",
                "-n",
                "base",
                "python",
                "/inspection.py",
                "--probe",
            ]
        )
    )
    if observation.get("execution") != "observed":
        raise ValueError("container_probe_failed")
    return observation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--context", default="default")
    parser.add_argument("--oci-report", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = {
        "format": "system-package-presence-v1",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "point_in_time": True,
        "package_deletion_performed": False,
        "exploitability": "not_established",
        "all_code_paths_inspected": False,
    }
    status = 0
    try:
        if args.probe:
            report.update(probe())
        else:
            if args.oci_report is None or args.output is None:
                raise ValueError("required_host_arguments_missing")
            proof = json.loads(args.oci_report.read_text())
            report["observation"] = host(args.context, proof)
            report["image_identity"] = {
                key: proof[key]
                for key in (
                    "source",
                    "architecture",
                    "config_digest",
                    "rootfs_diff_ids",
                )
            }
        report["execution"] = "observed"
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        IndexError,
        subprocess.SubprocessError,
    ):
        report["execution"] = "technical_failure"
        report["failure"] = "inspection_not_completed"
        status = 1
    text = json.dumps(report, indent=2) + "\n"
    if args.probe:
        print(text, end="")
    elif args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
    raise SystemExit(status)


if __name__ == "__main__":
    main()
