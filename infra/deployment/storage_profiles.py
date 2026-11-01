"""Disposable candidate configuration; never a pilot provider switch."""

from pathlib import Path
import secrets

IMAGES = {
    "minio": "minio/minio@sha256:14cea493d9a34af32f524e538b8346cf79f3321eff8e708c1e2960462bd8936e",
    "seaweedfs": "chrislusf/seaweedfs@sha256:f7a49e3f3972ebed5be2ed4befa4a0c68eb7bdddba6e692d42729ceb545134b8",
    "garage": "dxflrs/garage@sha256:677e5b758e4425a325b811c425c026bf35a4bf42f7ddbaa773de3f4fd779a5a5",
}


def command(kind, name):
    if kind == "minio":
        return ["server", "/data"]
    if kind == "seaweedfs":
        return ["mini", "-dir=/data", "-ip=" + name, "-ip.bind=0.0.0.0"]
    if kind == "garage":
        # Let the unchanged MinIO SDK create the bucket, not Garage bootstrap.
        return ["/garage", "server", "--single-node", "--default-access-key"]
    raise ValueError("unsupported_candidate")


def prepare(kind, name, root: Path, access, secret):
    args = command(kind, name)
    private_files = []
    if kind == "garage":
        config = root / "garage.toml"
        config.write_text(
            'metadata_dir = "/data/meta"\n'
            'data_dir = "/data/objects"\n'
            'db_engine = "sqlite"\n'
            "replication_factor = 1\n"
            "metadata_fsync = true\ndata_fsync = true\n"
            'rpc_bind_addr = "0.0.0.0:3901"\n'
            'rpc_public_addr = "127.0.0.1:3901"\n'
            f'rpc_secret = "{secrets.token_hex(32)}"\n'
            '[s3_api]\ns3_region = "us-east-1"\n'
            'api_bind_addr = "0.0.0.0:3900"\n'
        )
        config.chmod(0o600)
        private_files.append(config)
        environment = {
            "GARAGE_DEFAULT_ACCESS_KEY": access,
            "GARAGE_DEFAULT_SECRET_KEY": secret,
            # Initial bootstrap otherwise logs the access key at INFO.
            "RUST_LOG": "warn",
        }
        port = 3900
    elif kind == "seaweedfs":
        environment = {"AWS_ACCESS_KEY_ID": access, "AWS_SECRET_ACCESS_KEY": secret}
        port = 8333
    else:
        environment = {"MINIO_ROOT_USER": access, "MINIO_ROOT_PASSWORD": secret}
        port = 9000
    (root / "data").mkdir(exist_ok=True)
    return {
        "command": args,
        "environment": environment,
        "port": port,
        "private_files": private_files,
    }


def compose_definition(kind, side, project, root: Path, envfile: Path):
    name = project + "-" + side
    volumes = [{"type": "bind", "source": str(root / "data"), "target": "/data"}]
    if kind == "garage":
        volumes.append(
            {
                "type": "bind",
                "source": str(root / "garage.toml"),
                "target": "/etc/garage.toml",
                "read_only": True,
            }
        )
    return {
        "services": {
            side: {
                "image": IMAGES[kind],
                "container_name": name,
                "pull_policy": "never",
                "command": command(kind, name),
                "env_file": [str(envfile)],
                "labels": {"org.oligospace.disposable": project},
                "volumes": volumes,
            }
        },
        # The harness creates and verifies this unique --internal network.
        "networks": {"default": {"name": project, "external": True}},
    }
