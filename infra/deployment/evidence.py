"""No log payload leaves this check; Docker logs can use BOTH streams."""

import subprocess
import json


def candidate_runtime_report(docker, container):
    """Only fixed runtime categories leave the controller; no log text survives."""
    try:
        state = subprocess.run(
            docker + ["inspect", "--format", "{{json .State}}", container],
            capture_output=True,
            check=False,
            timeout=30,
        )
        if state.returncode:
            return {"status": "blocked", "rule_ids": ["CANDIDATE_INSPECTION_FAILED"]}
        running = json.loads(state.stdout).get("Running")
        if not isinstance(running, bool):
            return {"status": "blocked", "rule_ids": ["CANDIDATE_STATE_INVALID"]}
        logs = subprocess.run(
            docker + ["logs", container], capture_output=True, check=False, timeout=30
        )
        if logs.returncode:
            return {"status": "blocked", "rule_ids": ["CANDIDATE_LOG_RETRIEVAL_FAILED"]}
        payload = logs.stdout + logs.stderr
        if isinstance(payload, str):
            payload = payload.encode()
        rules = ["CANDIDATE_RUNNING" if running else "CANDIDATE_EXITED"]
        for pattern, rule in (
            (b"flag provided but not defined", "CANDIDATE_UNSUPPORTED_FLAG"),
            (b"permission denied", "CANDIDATE_PERMISSION_DENIED"),
            (b"read-only file system", "CANDIDATE_READ_ONLY_CONFIG"),
            (b"cannot unmarshal", "CANDIDATE_CONFIG_FORMAT_INVALID"),
            (b"address already in use", "CANDIDATE_PORT_CONFLICT"),
        ):
            if pattern in payload.lower():
                rules.append(rule)
        return {"status": "passed" if running else "failed", "rule_ids": rules}
    except Exception:
        return {"status": "blocked", "rule_ids": ["CANDIDATE_CONTROLLER_FAILED"]}


def credential_log_report(docker, container, access_identifiers, secret_values):
    """Classify in RAM only; preserve neither payload, matched value nor exception."""

    def blocked(rule):
        return {
            "status": "blocked",
            "rule_ids": [rule],
            "stdout_rule_ids": [],
            "stderr_rule_ids": [],
        }

    if (
        not isinstance(access_identifiers, list)
        or not isinstance(secret_values, list)
        or not access_identifiers + secret_values
        or any(
            not isinstance(value, str) or not value
            for value in access_identifiers + secret_values
        )
    ):
        return blocked("LOG_CONTROLLER_INPUT_INVALID")
    try:
        result = subprocess.run(
            docker + ["logs", container], capture_output=True, check=False, timeout=30
        )
    except subprocess.TimeoutExpired:
        return blocked("LOG_RETRIEVAL_TIMEOUT")
    except OSError:
        return blocked("LOG_CONTROLLER_EXECUTION_FAILED")
    except Exception:
        return blocked("LOG_CONTROLLER_FAILED")
    try:
        streams = {}
        for name, payload in (("stdout", result.stdout), ("stderr", result.stderr)):
            if isinstance(payload, str):
                payload = payload.encode("utf-8")
            if not isinstance(payload, bytes) or not isinstance(result.returncode, int):
                return blocked("LOG_CONTROLLER_RESULT_INVALID")
            streams[name + "_rule_ids"] = [
                rule
                for rule, values in (
                    ("LOG_ACCESS_IDENTIFIER_PRESENT", access_identifiers),
                    ("LOG_SECRET_VALUE_PRESENT", secret_values),
                )
                if any(value.encode("utf-8") in payload for value in values)
            ]
        matched = sorted(set(streams["stdout_rule_ids"] + streams["stderr_rule_ids"]))
        retrieval = ["LOG_RETRIEVAL_FAILED"] if result.returncode else []
        return {
            "status": "failed" if matched else "blocked" if retrieval else "passed",
            "rule_ids": retrieval + matched
            if retrieval or matched
            else ["LOG_NO_CREDENTIAL_MATCH"],
            **streams,
        }
    except Exception:
        return blocked("LOG_CONTROLLER_FAILED")


def credentials_absent_from_logs(
    docker: list[str], container: str, values: list[str]
) -> bool:
    # Historical callers keep the same strict gate; they do not need typed output.
    return credential_log_report(docker, container, [], values)["status"] == "passed"
