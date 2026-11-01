"""No log payload leaves this check; Docker logs can use BOTH streams."""

import subprocess


def credentials_absent_from_logs(
    docker: list[str], container: str, values: list[str]
) -> bool:
    result = subprocess.run(
        docker + ["logs", container], capture_output=True, text=True, check=False
    )
    return result.returncode == 0 and not any(
        value and value in (result.stdout + result.stderr) for value in values
    )
