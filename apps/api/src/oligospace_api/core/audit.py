from __future__ import annotations

import re
from contextvars import ContextVar
from typing import Any

request_id_context: ContextVar[str | None] = ContextVar("audit_request_id", default=None)
REQUEST_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")


def safe_audit_facts(value: Any) -> Any:
    """Copy structured facts while omitting credential and file-body values.

    This is defense in depth for structured metadata, not a secret detector for
    arbitrary prose. Callers must continue to choose safe bounded facts.
    """
    if isinstance(value, dict):
        result = {}
        for key, item in value.items():
            normalized = re.sub(r"[^a-z0-9]", "", str(key).casefold())
            sensitive = any(
                part in normalized
                for part in ("password", "secret", "token", "credential", "privatekey")
            ) or normalized in {
                "authorization",
                "cookie",
                "setcookie",
                "apikey",
                "body",
                "filebody",
                "filecontent",
                "filecontents",
                "rawfile",
                "sshkey",
                "signingkey",
            }
            result[key] = "[redacted]" if sensitive else safe_audit_facts(item)
        return result
    if isinstance(value, list):
        return [safe_audit_facts(item) for item in value]
    return value
