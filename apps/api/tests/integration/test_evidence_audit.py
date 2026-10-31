from __future__ import annotations

import json
import os
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_laboratory_routes import LaboratoryFixture

from oligospace_api.models.registry import AuditEvent

pytestmark = pytest.mark.skipif(
    "OLIGOSPACE_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL integration database is not configured",
)


@pytest.mark.parametrize(
    "operation",
    ["run_create", "run_update", "validation_create", "validation_supersede", "upload", "remove"],
)
async def test_evidence_audit_matrix(laboratory_client: LaboratoryFixture, operation: str) -> None:
    f = laboratory_client
    run_payload = {
        "assay_id": str(f.assay.id),
        "performed_at": "2026-10-31T09:00:00Z",
        "visibility": "organization",
    }
    run = await f.client.post("/api/v1/laboratory/runs", json=run_payload)
    assert run.status_code == 201
    validation_payload = {
        "assay_id": str(f.assay.id),
        "experiment_run_id": run.json()["id"],
        "status": "inconclusive",
        "conclusion": "Needs repetition",
        "validated_at": "2026-10-31T10:00:00Z",
    }
    validation = await f.client.post("/api/v1/laboratory/validations", json=validation_payload)
    assert validation.status_code == 201
    uploaded = None
    if operation == "remove":
        uploaded = await f.client.post(
            f"/api/v1/laboratory/run/{run.json()['public_id']}/attachments",
            files={"file": ("evidence.txt", b"private-file-marker", "text/plain")},
        )
        assert uploaded.status_code == 201
    async with async_sessionmaker(f.session.bind)() as session:
        previous = set((await session.scalars(select(AuditEvent.id))).all())
    request_id = f"evidence-{uuid.uuid4()}"
    headers = {"X-Request-ID": request_id}
    if operation == "run_create":
        result = await f.client.post("/api/v1/laboratory/runs", json=run_payload, headers=headers)
        expected = [("create", "experiment_run")]
    elif operation == "run_update":
        result = await f.client.patch(
            f"/api/v1/laboratory/runs/{run.json()['public_id']}",
            json={"status": "deprecated"},
            headers=headers,
        )
        expected = [("update", "experiment_run")]
    elif operation.startswith("validation"):
        body = {**validation_payload, "status": "passed", "conclusion": "Repeated successfully"}
        if operation == "validation_supersede":
            body["supersedes_validation_public_id"] = validation.json()["public_id"]
        result = await f.client.post("/api/v1/laboratory/validations", json=body, headers=headers)
        expected = [("create", "validation")]
        if operation == "validation_supersede":
            expected.append(("supersede", "validation"))
    elif operation == "upload":
        result = await f.client.post(
            f"/api/v1/laboratory/run/{run.json()['public_id']}/attachments",
            files={"file": ("evidence.txt", b"private-file-marker", "text/plain")},
            headers=headers,
        )
        expected = [("upload", "attachment")]
    else:
        assert uploaded is not None
        result = await f.client.delete(
            f"/api/v1/laboratory/attachments/{uploaded.json()['public_id']}", headers=headers
        )
        expected = [("remove", "attachment")]
    assert result.status_code in {200, 201}, result.text
    async with async_sessionmaker(f.session.bind)() as session:
        records = (
            await session.scalars(select(AuditEvent).where(AuditEvent.id.not_in(previous)))
        ).all()
        assert sorted((row.action, row.entity_type) for row in records) == sorted(expected)
        for row in records:
            assert row.actor_id == f.admin.id
            assert row.occurred_at.tzinfo is not None
            assert row.request_id == request_id
            assert "private-file-marker" not in json.dumps([row.before, row.after])
            assert row.entity_id == uuid.UUID(
                validation.json()["id"] if row.action == "supersede" else result.json()["id"]
            )
