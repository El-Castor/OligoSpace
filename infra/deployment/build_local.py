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


def loaded_image_matches(loaded: dict, proof: dict) -> bool:
    return loaded.get("Id") == proof.get("config_digest") and loaded.get(
        "RootFS", {}
    ).get("Layers") == proof.get("rootfs_diff_ids")


def validate_builder(
    info: dict, context: str, environment: dict, endpoint: str = ""
) -> bool:
    if any(
        environment.get(key)
        for key in ("DOCKER_HOST", "BUILDX_BUILDER", "BUILDKIT_HOST")
    ):
        return False
    nodes = info.get("Nodes", [])
    return (
        info.get("Driver") in ("docker", "docker-container")
        and len(nodes) == 1
        and nodes[0].get("Endpoint") in {context, endpoint}
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
    parser.add_argument("--builder")
    parser.add_argument("--role", choices=DOCKERFILES)
    parser.add_argument("--load-test-images", action="store_true")
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
    builder = args.builder or args.context
    info = parse_builder(
        subprocess.check_output(docker + ["buildx", "inspect", builder], text=True)
    )
    if not validate_builder(info, args.context, os.environ, endpoint):
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
    server_arch = subprocess.check_output(
        docker + ["info", "--format", "{{.Architecture}}"], text=True
    ).strip()
    native = {
        "aarch64": "arm64",
        "arm64": "arm64",
        "x86_64": "amd64",
        "amd64": "amd64",
    }.get(server_arch)
    manifest["mode"] = (
        "native_build" if native == args.architecture else "emulated_build_only"
    )
    with tempfile.TemporaryDirectory(prefix="oligospace-deploy01-build-") as directory:
        with tarfile.open(fileobj=io.BytesIO(archive)) as source:
            source.extractall(directory, filter="data")
        for role, file in DOCKERFILES.items():
            if args.role and role != args.role:
                continue
            artifact = output / f"{role}-{sha}-{args.architecture}.oci.tar"
            metadata = output / f"{role}-{sha}-{args.architecture}.metadata.json"
            subprocess.run(
                docker
                + [
                    "buildx",
                    "build",
                    "--builder",
                    builder,
                    "--platform",
                    "linux/" + args.architecture,
                    "--file",
                    str(Path(directory) / file),
                    "--tag",
                    f"oligospace-qualification/{role}:{sha}",
                    "--label",
                    "org.opencontainers.image.revision=" + sha,
                    "--provenance=mode=max",
                    "--sbom=generator=docker/buildkit-syft-scanner@sha256:873a7458c3c8ac8e32c7b796c10e1600b07b963d2aa000a72a2d97aaaa2d6315",
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
            from oci import verify_oci

            proof = verify_oci(artifact, args.architecture, sha)
            proof["role"] = role
            (output / f"{role}-oci-report.json").write_text(
                json.dumps(proof, indent=2) + "\n"
            )
            if args.load_test_images:
                subprocess.run(
                    docker
                    + [
                        "buildx",
                        "build",
                        "--builder",
                        builder,
                        "--platform",
                        "linux/" + args.architecture,
                        "--file",
                        str(Path(directory) / file),
                        "--label",
                        "org.opencontainers.image.revision=" + sha,
                        "--tag",
                        f"oligospace-qualification/{role}:{sha}",
                        "--provenance=false",
                        "--load",
                        directory,
                    ],
                    check=True,
                )
                loaded = json.loads(
                    subprocess.check_output(
                        docker
                        + [
                            "image",
                            "inspect",
                            f"oligospace-qualification/{role}:{sha}",
                        ],
                        text=True,
                    )
                )[0]
                if not loaded_image_matches(loaded, proof):
                    raise ValueError("loaded_image_does_not_match_verified_oci")
    (output / "qualification-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
