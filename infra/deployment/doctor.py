"""Local static diagnostic; no start/update/backup operation is implemented."""

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess

from policy import validate
from release import blockers, image_contract_matches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--env-file", type=Path, required=True)
    parser.add_argument("--project", required=True)
    parser.add_argument("--release-evidence", type=Path)
    args = parser.parse_args()
    try:
        if (
            not args.env_file.is_file()
            or stat.S_IMODE(args.env_file.stat().st_mode) & 0o077
        ):
            raise ValueError("protected_env_required")
        docker = ["docker", "--context", args.context]
        endpoint = json.loads(
            subprocess.check_output(
                docker + ["context", "inspect", args.context], stderr=subprocess.DEVNULL
            )
        )[0]["Endpoints"]["docker"]["Host"]
        if not endpoint.startswith("unix://") or os.environ.get("DOCKER_HOST"):
            raise ValueError("local_context_required")
        result = subprocess.run(
            docker
            + [
                "compose",
                "--project-name",
                args.project,
                "--env-file",
                str(args.env_file.resolve()),
                "--file",
                str(Path(__file__).with_name("compose.pilot.json")),
                "--profile",
                "operations",
                "config",
                "--format",
                "json",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode:
            raise ValueError("compose_preflight_failed")
        config = json.loads(result.stdout)
        rules = validate(config)
        manifest = (
            json.loads(args.release_evidence.read_text())
            if args.release_evidence
            else {}
        )
        pending = blockers(manifest)
        if not image_contract_matches(config, manifest):
            pending.append("manifest_config_images")
        print(
            json.dumps(
                {
                    "static": "failed" if rules else "passed",
                    "rules": rules,
                    "release": "blocked"
                    if pending
                    else "evidence_complete_pending_approval",
                    "unverified": pending,
                    "deployed": False,
                }
            )
        )
        return 1 if rules or pending else 0
    except Exception:
        print('{"static":"failed","rules":["preflight_refused"],"deployed":false}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
