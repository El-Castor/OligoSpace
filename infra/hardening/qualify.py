"""Native, disposable three-strategy OCI comparison; never publish or deploy."""

import argparse
import json
from pathlib import Path
import platform
import re
import subprocess
import sys

BASELINE = "9ebbf2cd993395af2b154efb0b4cf5a76b4dd079"
ROOT = Path(__file__).resolve().parents[2]


def valid_probe(value, role, architecture):
    return (
        isinstance(value, dict)
        and value.get("role") == role
        and value.get("actual_architecture") == architecture
        and value.get("status") in ("passed", "failed")
        and isinstance(value.get("reason_codes"), list)
        and all(isinstance(reason, str) for reason in value["reason_codes"])
        and (value["status"] == "passed") == (value["reason_codes"] == [])
    )


def invoke(command, *, capture=False):
    return subprocess.run(command, check=False, text=True, capture_output=capture)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--architecture", choices=("arm64", "amd64"), required=True)
    parser.add_argument("--role", choices=("api", "worker"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--vulnerability-cache", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.is_relative_to(ROOT):
        parser.error("artifact output must be outside the repository")
    docker = ["docker", "--context", args.context]
    engine = invoke(docker + ["info", "--format", "{{.Architecture}}"], capture=True)
    native = {
        "aarch64": "arm64",
        "arm64": "arm64",
        "x86_64": "amd64",
        "amd64": "amd64",
    }.get(engine.stdout.strip())
    if engine.returncode or native != args.architecture:
        parser.error(
            "native Docker architecture required; emulation is not qualification"
        )
    source = invoke(["git", "rev-parse", "HEAD"], capture=True).stdout.strip()
    if not re.fullmatch(r"[a-f0-9]{40}", source):
        parser.error("source commit required")
    output.mkdir(parents=True, exist_ok=True)
    summary = {
        "controller_source": source,
        "architecture": native,
        "host": platform.machine(),
        "role": args.role,
        "scope": "disposable_comparison_only",
        "publication_authorized": False,
        "profiles": {},
    }
    complete = True
    for profile in (
        "baseline",
        "strategy-a",
        "strategy-b",
        "strategy-c",
        "strategy-c-ubuntu",
    ):
        destination = output / profile
        destination.mkdir(exist_ok=True)
        revision = BASELINE if profile == "baseline" else source
        build = [
            sys.executable,
            str(ROOT / "infra/deployment/build_local.py"),
            "--context",
            args.context,
            "--architecture",
            native,
            "--role",
            args.role,
            "--load-test-images",
            "--output",
            str(destination),
        ]
        if profile == "baseline":
            build += ["--source-ref", BASELINE]
        else:
            build += ["--experiment", profile]
        result = invoke(build)
        record = {"source": revision, "build_exit": result.returncode}
        summary["profiles"][profile] = record
        if result.returncode:
            record["execution"] = "build_failed"
            complete = False
            continue
        archives = list(destination.glob("*.oci.tar"))
        if len(archives) != 1:
            raise ValueError("one_bound_OCI_artifact_required")
        record["oci_bytes"] = archives[0].stat().st_size
        scan = invoke(
            [
                sys.executable,
                str(ROOT / "infra/deployment/scan_artifact.py"),
                "--context",
                args.context,
                "--archive",
                str(archives[0]),
                "--architecture",
                native,
                "--source",
                revision,
                "--vulnerability-cache",
                str(args.vulnerability_cache.resolve()),
                "--output",
                str(destination / "scan.json"),
            ]
        )
        record["scan_exit"] = scan.returncode
        scan_data = json.loads((destination / "scan.json").read_text())
        record["scan_execution"] = scan_data.get("execution")
        record["release_scan_gate"] = scan_data.get("gate")
        if scan.returncode not in (0, 2) or not str(
            scan_data.get("execution", "")
        ).startswith("completed_"):
            complete = False
        suffix = "" if profile == "baseline" else "-" + profile
        image = f"oligospace-qualification/{args.role}{suffix}:{revision}"
        probe = invoke(
            docker
            + [
                "run",
                "--rm",
                "--platform",
                "linux/" + native,
                "--network",
                "none",
                "--read-only",
                "--cap-drop",
                "ALL",
                "--security-opt",
                "no-new-privileges",
                "--pids-limit",
                "128",
                "--memory",
                "768m",
                "--cpus",
                "2",
                "--tmpfs",
                "/tmp:rw,nosuid,nodev,size=128m,mode=1777",
                "--env",
                "PYTHONDONTWRITEBYTECODE=1",
                "--volume",
                f"{ROOT / 'infra/hardening/runtime_probe.py'}:/qualification/probe.py:ro",
                image,
                "python",
                "/qualification/probe.py",
                "--role",
                args.role,
                "--architecture",
                native,
                "--expect-hardened",
            ],
            capture=True,
        )
        # Never retain arbitrary exceptions or tool output from a failed entrypoint.
        try:
            probe_data = json.loads(probe.stdout)
            if not valid_probe(probe_data, args.role, native):
                raise ValueError("invalid_probe")
        except (json.JSONDecodeError, ValueError):
            probe_data = {
                "execution": "failed",
                "rule_id": "ENTRYPOINT_OR_PROBE_FAILED",
                "exit_code": probe.returncode,
            }
        (destination / "runtime.json").write_text(
            json.dumps(probe_data, indent=2) + "\n"
        )
        record["runtime_exit"] = probe.returncode
        record["runtime_gate"] = (
            "passed"
            if probe.returncode == 0 and probe_data.get("status") == "passed"
            else "failed"
        )
        # A rejected alternative is still an observed comparison. No strategy is
        # preselected; technical execution and suitability are separate decisions.
        if probe_data.get("rule_id") == "ENTRYPOINT_OR_PROBE_FAILED":
            complete = False
        record["execution"] = "completed"
        (output / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
    summary["technical_comparison"] = "completed" if complete else "incomplete"
    summary["release_authorization"] = "not_granted"
    (output / "comparison.json").write_text(json.dumps(summary, indent=2) + "\n")
    raise SystemExit(0 if complete else 1)


if __name__ == "__main__":
    main()
