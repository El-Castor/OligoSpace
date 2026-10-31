from __future__ import annotations

import json
import os
import uuid
from typing import Any

import pytest
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_assay_integrity import setup_assay
from test_workspace_routes import WorkspaceFixture, unique_dna

from oligospace_api.main import app
from oligospace_api.models.enums import GlobalRole
from oligospace_api.models.registry import AuditEvent, Oligo, ProjectMembership, Target
from oligospace_api.security.auth import _context_for_user, get_auth_context

pytestmark = pytest.mark.skipif(
    "OLIGOSPACE_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL integration database is not configured",
)


async def events(f: WorkspaceFixture) -> dict[uuid.UUID, dict[str, Any]]:
    async with async_sessionmaker(f.session.bind)() as session:
        records = (await session.scalars(select(AuditEvent))).all()
        return {
            item.id: {
                "actor": item.actor_id,
                "action": item.action,
                "entity": item.entity_type,
                "entity_id": item.entity_id,
                "time": item.occurred_at,
                "request": item.request_id,
                "before": item.before,
                "after": item.after,
            }
            for item in records
        }


@pytest.mark.parametrize(
    "case",
    [
        "oligo_create",
        "oligo_update",
        "oligo_deprecated",
        "oligo_archived",
        "target_create",
        "target_update",
        "target_deprecated",
        "target_archived",
        "assay_create",
        "assay_update",
        "assay_deprecated",
        "assay_archived",
        "method_create",
        "method_update",
        "organism_create",
        "organism_update",
        "user_create",
        "user_update",
        "profile_update",
        "team_create",
        "team_update",
        "team_add_member",
        "team_change_member_role",
        "team_remove_member",
        "project_create",
        "project_update",
        "project_deprecated",
        "project_archived",
        "project_add_member",
        "project_change_member_role",
        "project_remove_member",
    ],
)
async def test_mutation_audit_matrix(workspace_client: WorkspaceFixture, case: str) -> None:
    f = workspace_client
    client = f.client
    payload = await setup_assay(f)
    assay_response = await client.post("/api/v1/registry/assays", json=payload)
    assert assay_response.status_code == 201
    assay = assay_response.json()
    team_response = await client.post("/api/v1/workspace/teams", json={"name": uuid.uuid4().hex})
    assert team_response.status_code == 201
    team = team_response.json()
    project_response = await client.post(
        "/api/v1/workspace/projects", json={"name": uuid.uuid4().hex}
    )
    assert project_response.status_code == 201
    project = project_response.json()
    organism_response = await client.post(
        "/api/v1/registry/organisms", json={"scientific_name": uuid.uuid4().hex}
    )
    assert organism_response.status_code == 201
    organism = organism_response.json()
    # Setup existing memberships only when a change/removal is requested.
    kind, operation = case.split("_", 1)
    if operation in {"change_member_role", "remove_member"}:
        workspace = team if kind == "team" else project
        key = workspace["id"] if kind == "team" else workspace["public_id"]
        added = await client.put(
            f"/api/v1/workspace/{kind}s/{key}/members/{f.member.id}", json={"role": "member"}
        )
        assert added.status_code == 200
    method = "PATCH"
    body: dict[str, Any] = {"name": f"Audit update {uuid.uuid4().hex}"}
    action = "create" if operation == "create" else "update"
    entity = kind
    expected_id = None
    if kind in {"oligo", "target", "assay"}:
        plural = {"oligo": "oligos", "target": "targets", "assay": "assays"}[kind]
        record = (
            assay
            if kind == "assay"
            else {"id": payload["target_id"]}
            if kind == "target"
            else {"id": payload["oligos"][0]["oligo_id"]}
        )
        if kind != "assay":
            obj = await f.session.get(Oligo if kind == "oligo" else Target, uuid.UUID(record["id"]))
            assert obj is not None
            record["public_id"] = obj.public_id
        path = f"/api/v1/registry/{plural}/{record['public_id']}"
        expected_id = record["id"]
        if operation == "create":
            method, path = "POST", f"/api/v1/registry/{plural}"
            body = {"name": "New audited record", "visibility": "private"}
            if kind == "oligo":
                body["sequence"] = unique_dna()
            if kind == "assay":
                body = {**payload, "name": "New audited assay"}
        elif operation in {"deprecated", "archived"}:
            body = {"status": operation}
    elif kind in {"method", "organism"}:
        plural = "experiment-types" if kind == "method" else "organisms"
        entity = "experiment_type" if kind == "method" else "organism"
        expected_id = payload["experiment_type_id"] if kind == "method" else organism["id"]
        path = f"/api/v1/registry/{plural}/{expected_id}"
        body = (
            {"description": "Audited catalogue update"}
            if kind == "method"
            else {"common_name": "Audited organism"}
        )
        if operation == "create":
            method, path = "POST", f"/api/v1/registry/{plural}"
            body = (
                {"name": uuid.uuid4().hex, "slug": uuid.uuid4().hex}
                if kind == "method"
                else {"scientific_name": uuid.uuid4().hex}
            )
    elif kind in {"user", "profile"}:
        entity = "user"
        expected_id = str(f.admin.id if kind == "profile" else f.member.id)
        path = (
            "/api/v1/workspace/profile"
            if kind == "profile"
            else f"/api/v1/workspace/admin/users/{expected_id}"
        )
        body = {"display_name": "Audited identity"}
        if kind == "profile":
            action = "update_profile"
        if operation == "create":
            method, path = "POST", "/api/v1/workspace/admin/users"
            body = {
                "external_identity_id": uuid.uuid4().hex,
                "email": f"{uuid.uuid4().hex}@audit.test",
                "display_name": "Audited user",
            }
    else:
        record = team if kind == "team" else project
        expected_id = record["id"]
        key = record["id"] if kind == "team" else record["public_id"]
        path = f"/api/v1/workspace/{kind}s/{key}"
        if operation == "create":
            method, path = "POST", f"/api/v1/workspace/{kind}s"
        elif operation in {"deprecated", "archived"}:
            body = {"status": operation}
        elif "member" in operation:
            entity, action = f"{kind}_membership", operation
            path += f"/members/{f.member.id}"
            method = "DELETE" if operation == "remove_member" else "PUT"
            body = {"role": "team_manager"}
    before = await events(f)
    request_id = f"audit-{uuid.uuid4()}"
    response = await client.request(
        method,
        path,
        json=body if method != "DELETE" else None,
        headers={
            "X-Request-ID": request_id,
            "Authorization": "Bearer never-store-header",
            "Cookie": "never-store-cookie",
        },
    )
    assert response.status_code in {200, 201, 204}, response.text
    added = {key: value for key, value in (await events(f)).items() if key not in before}
    assert len(added) == 1
    event = next(iter(added.values()))
    if operation == "create":
        record = response.json()["oligo"] if kind == "oligo" else response.json()
        expected_id = record["id"]
    assert event["actor"] == f.admin.id
    assert event["entity"] == entity
    assert event["action"] == action
    assert str(event["entity_id"]) == expected_id
    assert event["time"].tzinfo is not None
    assert event["request"] == request_id
    assert response.headers["X-Request-ID"] == request_id
    serialized = json.dumps(event, default=str)
    assert "never-store-header" not in serialized
    assert "never-store-cookie" not in serialized
    # Existing evidence remains append-oriented and unchanged after every mutation.
    after = await events(f)
    assert all(after[key] == value for key, value in before.items())


async def test_nested_sensitive_audit_facts_are_redacted(
    workspace_client: WorkspaceFixture,
) -> None:
    f = workspace_client
    payload = await setup_assay(f)
    created = await f.client.post("/api/v1/registry/assays", json=payload)
    assert created.status_code == 201
    before = await events(f)
    response = await f.client.patch(
        f"/api/v1/registry/assays/{created.json()['public_id']}",
        json={
            "method_metadata": {
                "protocol": "safe",
                "nested": [
                    {
                        "access_token": "secret-marker",
                        "client-secret": "secret-marker",
                        "file_body": "file-marker",
                    }
                ],
            }
        },
    )
    assert response.status_code == 200
    added = [value for key, value in (await events(f)).items() if key not in before]
    assert len(added) == 1
    serialized = json.dumps(added, default=str)
    assert "secret-marker" not in serialized
    assert "file-marker" not in serialized
    assert added[0]["after"]["method_metadata"]["protocol"] == "safe"


async def test_recent_activity_does_not_disclose_revoked_resource(
    workspace_client: WorkspaceFixture,
) -> None:
    f = workspace_client
    payload = await setup_assay(f)
    project = await f.client.post("/api/v1/workspace/projects", json={"name": uuid.uuid4().hex})
    assert project.status_code == 201
    project_id = uuid.UUID(project.json()["id"])
    payload.update(visibility="project", project_id=str(project_id))
    created = await f.client.post("/api/v1/registry/assays", json=payload)
    assert created.status_code == 201
    assay = created.json()
    f.session.add(
        ProjectMembership(project_id=project_id, user_id=f.member.id, role=GlobalRole.TEAM_MANAGER)
    )
    await f.session.commit()

    async def member_identity():
        return await _context_for_user(f.session, f.member, development_identity=False)

    app.dependency_overrides[get_auth_context] = member_identity
    updated = await f.client.patch(
        f"/api/v1/registry/assays/{assay['public_id']}", json={"name": "Manager edit"}
    )
    assert updated.status_code == 200

    await f.session.execute(
        delete(ProjectMembership).where(
            ProjectMembership.project_id == project_id, ProjectMembership.user_id == f.member.id
        )
    )
    await f.session.commit()
    dashboard = await f.client.get("/api/v1/workspace/dashboard")
    assert dashboard.status_code == 200
    assert assay["id"] not in json.dumps(dashboard.json())
    assert assay["public_id"] not in json.dumps(dashboard.json())
