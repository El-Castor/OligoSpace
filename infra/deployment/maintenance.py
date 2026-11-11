"""Guarded disposable maintenance; delegates recovery, never installs a real pilot."""

import argparse
import json
from pathlib import Path
import re
import sys

from bootstrap import HEAD
from doctor import protected_file


def disposable_project(project):
    return bool(re.fullmatch(r"oligospace-pilot-test-[a-z0-9-]+", project))


def revision_status(revisions):
    return "PASS" if revisions == [HEAD] else "BLOCKED"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action", choices=["pre-migration", "backup", "restore", "activation-check"]
    )
    parser.add_argument("--recovery-config", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--key-file", type=Path)
    args = parser.parse_args()
    report = {"status": "BLOCKED", "deployed": False, "migration_executed": False}
    try:
        if not protected_file(args.recovery_config, secret=True):
            raise ValueError("private_config_required")
        config = json.loads(args.recovery_config.read_text())
        if (
            not disposable_project(config.get("project", ""))
            or args.action == "activation-check"
        ):
            print(json.dumps(report))
            return 1
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backup"))
        from recovery import Recovery

        operation = Recovery(config)
        if args.action == "pre-migration":
            operation._preflight()
            revisions = operation._sql(
                "application",
                "SELECT version_num FROM alembic_version ORDER BY version_num",
            ).splitlines()
            report["status"] = revision_status(revisions)
        else:
            if args.archive is None or args.key_file is None:
                raise ValueError("recovery_inputs_required")
            result = getattr(operation, args.action)(args.archive, args.key_file)
            report.update(status="PASS", recovery=result)
    except Exception:
        report["status"] = "FAIL"
    print(json.dumps(report))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
