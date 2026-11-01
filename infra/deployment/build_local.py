"""Export SHA-versioned OCI qualification artifacts from tracked Git sources.

No registry push. No production readiness assertion. Requires an explicitly local
Docker context and an output directory outside the repository. Registry choice,
publication and native cross-architecture qualification remain separate gates.
"""

import argparse
import io
import json
import os
import re
from pathlib import Path
import subprocess
import tarfile
import tempfile

DOCKERFILES = {
    "api": "infra/docker/api/Dockerfile",
    "web": "infra/docker/web/Dockerfile",
    "worker": "infra/docker/bioinfo-worker.Dockerfile",
}


def validate_builder(info: dict, context: str, environment: dict) -> bool:
    if any(
        environment.get(key)
        for key in ("DOCKER_HOST", "BUILDX_BUILDER", "BUILDKIT_HOST")
    ):
        return False
    nodes = info.get("Nodes", [])
    return (
        info.get("Driver") == "docker"
        and len(nodes) == 1
        and nodes[0].get("Endpoint") == context
    )


def parse_builder(text: str) -> dict:
    drivers = re.findall(r"^Driver:\s+(\S+)\s*$", text, re.MULTILINE)
    endpoints = re.findall(r"^Endpoint:\s+(\S+)\s*$", text, re.MULTILINE)
    return {
        "Driver": drivers[0] if len(drivers) == 1 else "invalid",
        "Nodes": [{"Endpoint": endpoint} for endpoint in endpoints],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--context", required=True)
    parser.add_argument("--architecture", choices=["arm64", "amd64"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    output = args.output.resolve()
    if output.is_relative_to(repo):
        parser.error("output must be outside repository")
    docker = ["docker", "--context", args.context]
    endpoint = json.loads(
        subprocess.check_output(docker + ["context", "inspect", args.context])
    )[0]["Endpoints"]["docker"]["Host"]
    if not endpoint.startswith("unix://"):
        parser.error("local unix context required")
    info = parse_builder(
        subprocess.check_output(docker + ["buildx", "inspect", args.context], text=True)
    )
    if not validate_builder(info, args.context, os.environ):
        parser.error("explicit local docker builder required; overrides refused")
    subprocess.run(["git", "diff", "--quiet", "HEAD"], cwd=repo, check=True)
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()
    archive = subprocess.check_output(["git", "archive", sha], cwd=repo)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "source": sha,
        "status": "qualification_only",
        "architecture": args.architecture,
        "mode": "native_or_emulated_unqualified",
        "images": {},
        "shared_roles": {"migrate": "api", "scheduler": "worker"},
    }
    with tempfile.TemporaryDirectory(prefix="oligospace-deploy01-build-") as directory:
        with tarfile.open(fileobj=io.BytesIO(archive)) as source:
            source.extractall(directory, filter="data")
        for role, file in DOCKERFILES.items():
            artifact = output / f"{role}-{sha}-{args.architecture}.oci.tar"
            metadata = output / f"{role}-{sha}-{args.architecture}.metadata.json"
            subprocess.run(
                docker
                + [
                    "buildx",
                    "build",
                    "--builder",
                    args.context,
                    "--platform",
                    "linux/" + args.architecture,
                    "--file",
                    str(Path(directory) / file),
                    "--tag",
                    f"oligospace-qualification/{role}:{sha}",
                    "--label",
                    "org.opencontainers.image.revision=" + sha,
                    "--provenance=mode=max",
                    "--sbom=true",
                    "--metadata-file",
                    str(metadata),
                    "--output",
                    f"type=oci,dest={artifact}",
                    directory,
                ],
                check=True,
            )
            digest = json.loads(metadata.read_text()).get("containerimage.digest")
            manifest["images"][role] = {
                "digest": digest,
                "artifact": artifact.name,
                "metadata": metadata.name,
            }
    (output / "qualification-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
