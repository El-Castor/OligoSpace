import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient

from oligospace_api.core.audit import request_id_context, safe_audit_facts
from oligospace_api.main import app


def test_audit_redaction_is_recursive_and_does_not_modify_source() -> None:
    source = {
        "protocol": "safe",
        "children": [
            {
                "API-Key": "secret",
                "password": "secret",
                "refresh_token": "secret",
                "file_body": "file",
            }
        ],
    }
    safe = safe_audit_facts(source)
    assert safe == {
        "protocol": "safe",
        "children": [
            {
                "API-Key": "[redacted]",
                "password": "[redacted]",
                "refresh_token": "[redacted]",
                "file_body": "[redacted]",
            }
        ],
    }
    assert source["children"][0]["password"] == "secret"


@pytest.mark.parametrize("key", ["private_key", "privateKey", "credentials", "APIKey"])
def test_structured_credential_keys_are_redacted(key: str) -> None:
    assert safe_audit_facts({key: "credential-marker"}) == {key: "[redacted]"}


@pytest.mark.parametrize("supplied", [None, "bad value", "x" * 81])
async def test_request_ids_are_generated_without_echoing_invalid_values(
    supplied: str | None,
) -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/health/live", headers={"X-Request-ID": supplied} if supplied else {}
        )
        assert response.status_code == 200
        assert str(uuid.UUID(response.headers["X-Request-ID"])) == response.headers["X-Request-ID"]
        assert request_id_context.get() is None


async def test_concurrent_request_correlation_is_isolated() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        ids = [f"isolated-{index}" for index in range(5)]
        responses = await asyncio.gather(
            *(client.get("/api/v1/health/live", headers={"X-Request-ID": value}) for value in ids)
        )
        assert [response.headers["X-Request-ID"] for response in responses] == ids
        assert request_id_context.get() is None
