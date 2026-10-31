from __future__ import annotations

import os
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_assay_integrity import setup_assay
from test_workspace_routes import WorkspaceFixture, unique_dna

from oligospace_api.models.registry import Assay, AuditEvent, Oligo, Project, Target

pytestmark = pytest.mark.skipif(
    "OLIGOSPACE_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL integration database is not configured",
)


@pytest.mark.parametrize(
    "entity,model,prefix",
    [
        ("oligo", Oligo, "/api/v1/registry/oligos"),
        ("target", Target, "/api/v1/registry/targets"),
        ("assay", Assay, "/api/v1/registry/assays"),
        ("project", Project, "/api/v1/workspace/projects"),
    ],
)
async def test_lifecycle_retains_identity_and_audit(
    workspace_client: WorkspaceFixture,
    entity,
    model,
    prefix: str,
) -> None:
    f = workspace_client
    body = {"name": f"Lifecycle {uuid.uuid4().hex}"}
    if entity == "oligo":
        body["sequence"] = unique_dna()
    if entity == "assay":
        body = await setup_assay(f)
    response = await f.client.post(prefix, json=body)
    assert response.status_code == 201
    record = response.json()["oligo"] if entity == "oligo" else response.json()
    path = f"{prefix}/{record['public_id']}"
    record_id = uuid.UUID(record["id"])
    for version, status in enumerate(["deprecated", "archived"], start=2):
        result = await f.client.patch(path, json={"status": status})
        assert result.status_code == 200
        async with async_sessionmaker(f.session.bind)() as session:
            saved = await session.get(model, record_id)
            assert saved is not None
            assert saved.status.value == status
            assert saved.public_id == record["public_id"]
            if entity == "assay":
                assert saved.version == version
                assert len(saved.oligos) == 1
                link = saved.oligos[0]
                expected_link = body["oligos"][0]
                assert str(link.oligo_id) == expected_link["oligo_id"]
                assert link.role.value == expected_link["role"]
                assert link.label == expected_link["label"]
            audits = (
                await session.scalars(
                    select(AuditEvent)
                    .where(AuditEvent.entity_type == entity, AuditEvent.entity_id == record_id)
                    .order_by(AuditEvent.occurred_at)
                )
            ).all()
            assert len(audits) == version
            assert [event.action for event in audits] == ["create"] + ["update"] * (version - 1)
            assert audits[-1].before["status"] == ("active" if version == 2 else "deprecated")
            assert audits[-1].after["status"] == status
            assert all(event.actor_id == f.admin.id and event.request_id for event in audits)
        detail = await f.client.get(path)
        assert detail.status_code == 200
        assert detail.json()["status"] == status
        # Stable identity cannot be reassigned, even after deprecation/archive.
        renamed = await f.client.patch(path, json={"public_id": "OLG-999999999"})
        assert renamed.status_code == 422
        invalid = await f.client.patch(path, json={"status": "deleted"})
        assert invalid.status_code == 422
    if entity == "oligo":
        duplicate = await f.client.post(prefix, json=body)
        assert duplicate.status_code == 409
        assert duplicate.json()["detail"]["existing_public_id"] == record["public_id"]
        body["sequence"] = unique_dna()
    new = await f.client.post(prefix, json=body)
    assert new.status_code == 201
    new_record = new.json()["oligo"] if entity == "oligo" else new.json()
    assert new_record["id"] != record["id"]
    assert new_record["public_id"] != record["public_id"]
    old = await f.client.get(path)
    assert old.status_code == 200
    assert old.json()["status"] == "archived"
    async with async_sessionmaker(f.session.bind)() as session:
        audit_count = len(
            (
                await session.scalars(
                    select(AuditEvent.id).where(
                        AuditEvent.entity_type == entity, AuditEvent.entity_id == record_id
                    )
                )
            ).all()
        )
        assert audit_count == 3  # rejected mutations added no business audit.
