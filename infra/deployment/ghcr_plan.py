"""Dry-run naming/permission contract. No network, login, push or package API."""

import argparse
import json
import re


def publication_plan(repository, source):
    if not re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository
    ) or not re.fullmatch(r"[a-f0-9]{40}", source):
        raise ValueError("invalid_repository_or_source")
    prefix = "ghcr.io/" + repository.lower()
    return {
        "mode": "dry_run_only",
        "source": source,
        "proposed_registry": prefix,
        "images": {
            role: prefix + "/" + role + ":sha-" + source
            for role in ("api", "web", "worker")
        },
        "shared_roles": {"migrate": "api", "scheduler": "worker"},
        "publishing_authorized": False,
        "packages_created": False,
        "requires_decision": [
            "package_visibility",
            "Actions_publish_permission",
            "signing",
            "retention",
            "recovery",
            "reader_revocation",
            "storage_license",
        ],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--source", required=True)
    args = parser.parse_args()
    print(json.dumps(publication_plan(args.repository, args.source), indent=2))
