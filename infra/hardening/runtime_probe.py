"""Run inside a disposable candidate; emit observations without credentials."""

import argparse
import errno
import importlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import ssl
import subprocess
import sys
import tempfile


def status_fields(status: str) -> dict:
    return dict(line.split(":", 1) for line in status.splitlines() if ":" in line)


def hardened_status(status: str) -> bool:
    fields = status_fields(status)
    return (
        "CapEff" in fields
        and int(fields["CapEff"].strip(), 16) == 0
        and fields.get("NoNewPrivs", "").strip() == "1"
    )


def readonly_root_proven(mounts: str, write_errno: int | None) -> bool:
    root_options = [
        fields[3].split(",")
        for line in mounts.splitlines()
        if len(fields := line.split()) >= 4 and fields[1] == "/"
    ]
    return (
        len(root_options) == 1
        and "ro" in root_options[0]
        and "rw" not in root_options[0]
        and write_errno in (errno.EROFS, errno.EACCES)
    )


def run(arguments: list[str], timeout: float = 30) -> subprocess.CompletedProcess:
    return subprocess.run(
        arguments, capture_output=True, text=True, timeout=timeout, check=True
    )


def elf(path: Path) -> bool:
    try:
        with path.open("rb") as stream:
            return stream.read(4) == b"\x7fELF"
    except OSError:
        return False


def bundled_library_root(path: Path) -> Path | None:
    """Only wheel-owned sibling libraries may supply contextual loader paths."""
    resolved = path.resolve()
    for pattern in (
        "lib/python*/site-packages/*.libs",
        "lib64/python*/site-packages/*.libs",
    ):
        for root in Path(sys.prefix).glob(pattern):
            if root.is_dir() and resolved.is_relative_to(root.resolve()):
                return root.resolve()
    return None


def ldd_unclassified(result: subprocess.CompletedProcess, output: str) -> bool:
    return bool(result.returncode) and not any(
        text in output for text in ("not a dynamic executable", "statically linked")
    )


def native_libraries() -> dict:
    roots = {
        Path(sys.prefix),
        Path(sys.base_prefix),
        Path("/opt/primer3/bin"),
        Path("/opt/ncbi-blast"),
    }
    files = {Path(sys.executable).resolve()}
    for root in roots:
        if root.exists():
            files.update(
                path for path in root.rglob("*") if path.is_file() and elf(path)
            )
    missing = []
    unclassified = []
    first_pass_missing = []
    contextual_checks = []
    for path in sorted(files):
        result = subprocess.run(
            ["ldd", str(path)], capture_output=True, text=True, timeout=10
        )
        output = result.stdout + result.stderr
        if "not found" in output:
            first_pass_missing.append({"path": str(path), "output": output})
            bundle = bundled_library_root(path)
            if bundle is not None:
                # Do not inherit an unrelated LD_LIBRARY_PATH or borrow system/other
                # wheel directories. A successful import separately proves activation.
                environment = dict(os.environ, LD_LIBRARY_PATH=str(bundle))
                contextual = subprocess.run(
                    ["ldd", str(path)],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    env=environment,
                )
                remaining = contextual.stdout + contextual.stderr
                contextual_checks.append(
                    {
                        "path": str(path),
                        "library_path": str(bundle),
                        "output": remaining,
                        "returncode": contextual.returncode,
                        "resolved": contextual.returncode == 0
                        and "not found" not in remaining,
                    }
                )
                result, output = contextual, remaining
            if "not found" in output or (bundle is not None and result.returncode != 0):
                missing.append(str(path))
        if ldd_unclassified(result, output):
            unclassified.append(str(path))
    return {
        "elf_files_checked": len(files),
        "first_pass_missing": first_pass_missing,
        "contextual_checks": contextual_checks,
        "missing_libraries": missing,
        "unclassified": unclassified,
    }


def native_imports(role: str) -> dict[str, bool]:
    modules = (
        ("psycopg", "psycopg_binary", "Bio", "numpy")
        if role == "worker"
        else ("asyncpg", "cryptography.hazmat.bindings._rust")
    )
    results = {}
    for module in modules:
        try:
            importlib.import_module(module)
            results[module] = True
        except Exception:
            results[module] = False
    return results


def worker_checks() -> dict:
    from oligospace_bioinfo import tasks

    parameters = {
        "mv_conc_mM": 50.0,
        "dv_conc_mM": 1.5,
        "dntp_conc_mM": 0.6,
        "dna_conc_nM": 50.0,
        "max_loop": 30,
        "max_nn_length": 60,
        "tm_method": "santalucia_1998",
        "salt_correction_method": "santalucia_1998",
    }
    result = tasks.primer3_analysis(
        "assay_primer3_pair_compatibility",
        {
            "forward": {"normalized_sequence": "ATGCGTACGTTAGCGTACGA"},
            "reverse": {"normalized_sequence": "TCGTACGCTAACGTACGCAT"},
        },
        parameters,
    )
    payload = result["payload"]
    observed = [
        payload[side][key]["value"]
        for side in ("forward", "reverse")
        for key in ("nearest_neighbor_tm", "hairpin", "homodimer")
    ]
    observed += [
        payload[key]["value"]
        for key in ("tm_delta", "heterodimer", "end_complementarity")
    ]
    expected = [
        59.626630,
        69.836183,
        46.168760,
        59.626630,
        69.091431,
        34.346077,
        0.0,
        59.555182,
        59.555182,
    ]
    golden = all(
        math.isclose(value, target, rel_tol=0, abs_tol=1e-6)
        for value, target in zip(observed, expected, strict=True)
    )
    golden = (
        golden and result["interpretation"] is None and tasks.PRIMER3_VERSION == "2.6.1"
    )
    golden = (
        golden
        and tasks.PRIMER3_SOURCE_SHA256
        == "805cef7ef39607cd40f0f5bb8b32e35e20007153a0a55131dd430ce644c8fb9e"
    )
    failures = {}
    previous = os.environ.get("SCIENTIFIC_TOOL_TIMEOUT_SECONDS")
    try:
        os.environ["SCIENTIFIC_TOOL_TIMEOUT_SECONDS"] = "0.05"
        for name, code in (
            ("timeout", "import time; time.sleep(2)"),
            ("exit", "raise SystemExit(7)"),
        ):
            try:
                tasks._run_tool([sys.executable, "-c", code])
                failures[name] = False
            except tasks.ScientificToolError as error:
                failures[name] = error.code == "tool_" + name
    finally:
        if previous is None:
            os.environ.pop("SCIENTIFIC_TOOL_TIMEOUT_SECONDS", None)
        else:
            os.environ["SCIENTIFIC_TOOL_TIMEOUT_SECONDS"] = previous
    versions = {}
    for tool in sorted(Path("/opt/ncbi-blast/bin").iterdir()):
        if elf(tool):
            try:
                output = run([str(tool), "-version"], 10).stdout
                versions[tool.name] = "2.17.0" in output
            except (subprocess.SubprocessError, OSError):
                versions[tool.name] = None
    with tempfile.TemporaryDirectory(
        prefix="oligospace-synthetic-", dir="/tmp"
    ) as directory:
        fixture = Path(directory) / "synthetic.fa"
        sequence = "ACGTTGCAAGTCGATCGTACGATGCTAGCTAGGCTAACGTTCGATGCA"
        fixture.write_text(">synthetic\n" + sequence + "\n")
        database = str(Path(directory) / "db")
        run(["makeblastdb", "-in", str(fixture), "-dbtype", "nucl", "-out", database])
        hits = run(
            [
                "blastn",
                "-query",
                str(fixture),
                "-db",
                database,
                "-dust",
                "no",
                "-outfmt",
                "6 qseqid sseqid pident length",
            ]
        ).stdout.splitlines()
        match = f"synthetic\tsynthetic\t100.000\t{len(sequence)}" in hits
    return {
        "primer3_nine_golden_facts": golden,
        "primer3_observed_values": observed,
        "primer3_reference_values": expected,
        "primer3_parameters": parameters,
        "primer3_source_sha256": tasks.PRIMER3_SOURCE_SHA256,
        "primer3_version": tasks.PRIMER3_VERSION,
        "tool_failure_classification": failures,
        "blast_version_checks": versions,
        "blast_version_scope": "ELF tools accepting -version only",
        "blast_synthetic_exact_match": match,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=("api", "worker"), required=True)
    parser.add_argument("--architecture", choices=("arm64", "amd64"), required=True)
    parser.add_argument("--expect-hardened", action="store_true")
    args = parser.parse_args()
    report = {"role": args.role, "expected_hardened": args.expect_hardened}
    reasons = []
    try:
        architecture = {"aarch64": "arm64", "x86_64": "amd64"}.get(
            platform.machine(), "unknown"
        )
        report.update(
            actual_architecture=architecture,
            uid=os.getuid(),
            gid=os.getgid(),
            python=platform.python_version(),
        )
        if architecture != args.architecture:
            reasons.append("architecture_mismatch")
        fields = status_fields(Path("/proc/self/status").read_text())
        report.update(
            cap_eff=fields.get("CapEff", "").strip(),
            no_new_privs=fields.get("NoNewPrivs", "").strip(),
        )
        write_errno = None
        probe = Path("/etc/oligospace-write-probe")
        try:
            with probe.open("xb"):
                pass
            probe.unlink()
        except OSError as error:
            write_errno = error.errno
        mounts = Path("/proc/mounts").read_text()
        read_only = readonly_root_proven(mounts, write_errno)
        report["rootfs_erofs"] = write_errno == errno.EROFS
        report["rootfs_write_errno"] = errno.errorcode.get(write_errno, "none")
        report["rootfs_readonly_proven"] = read_only
        with tempfile.TemporaryFile(dir="/tmp") as temporary:
            temporary.write(b"probe")
        report["tmp_writable"] = True
        report["ca_certificates"] = len(ssl.create_default_context().get_ca_certs())
        if not report["ca_certificates"]:
            reasons.append("ca_store_empty")
        report["kombu"] = importlib.metadata.version("kombu")
        importlib.import_module(
            "oligospace_api.main" if args.role == "api" else "oligospace_bioinfo.tasks"
        )
        report["role_import"] = True
        report["role_version"] = importlib.metadata.version(
            "oligospace-api" if args.role == "api" else "oligospace-bioinfo"
        )
        if report["kombu"] != "5.6.2" or sys.version_info[:2] != (3, 12):
            reasons.append("runtime_version_mismatch")
        report["native_imports"] = native_imports(args.role)
        if not all(report["native_imports"].values()):
            reasons.append("native_import_check_failed")
        report["native_libraries"] = native_libraries()
        if (
            report["native_libraries"]["missing_libraries"]
            or report["native_libraries"]["unclassified"]
        ):
            reasons.append("native_library_check_failed")
        if args.expect_hardened and (
            os.getuid() == 0
            or not hardened_status(Path("/proc/self/status").read_text())
            or not read_only
        ):
            reasons.append("hardening_check_failed")
        if args.role == "worker":
            report["scientific_library_versions"] = {
                "biopython": importlib.metadata.version("biopython"),
                "numpy": importlib.metadata.version("numpy"),
            }
            report["scientific_checks"] = checks = worker_checks()
            if not (
                checks["primer3_nine_golden_facts"]
                and all(checks["tool_failure_classification"].values())
                and checks["blast_synthetic_exact_match"]
                and checks["blast_version_checks"].get("blastn")
                and checks["blast_version_checks"].get("makeblastdb")
                and all(
                    value is not False
                    for value in checks["blast_version_checks"].values()
                )
            ):
                reasons.append("scientific_check_failed")
    except Exception:
        reasons.append("probe_execution_failed")
    report.update(status="failed" if reasons else "passed", reason_codes=reasons)
    print(json.dumps(report, sort_keys=True))
    return int(bool(reasons))


if __name__ == "__main__":
    raise SystemExit(main())
