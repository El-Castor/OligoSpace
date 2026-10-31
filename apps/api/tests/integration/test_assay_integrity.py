from __future__ import annotations

import os
import uuid
from typing import Any

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_workspace_routes import WorkspaceFixture, unique_dna

from oligospace_api.main import app
from oligospace_api.models.enums import GlobalRole
from oligospace_api.models.registry import (
    Assay,
    AssayOligo,
    AuditEvent,
    Oligo,
    Organization,
    ProjectMembership,
    Target,
)
from oligospace_api.security.auth import _context_for_user, get_auth_context

pytestmark = pytest.mark.skipif(
    "OLIGOSPACE_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL integration database is not configured",
)


async def setup_assay(f: WorkspaceFixture) -> dict[str, Any]:
    method = await f.client.post(
        "/api/v1/registry/experiment-types",
        json={
            "name": uuid.uuid4().hex,
            "slug": uuid.uuid4().hex,
            "allowed_roles": ["forward_primer", "reverse_primer"],
        },
    )
    assert method.status_code == 201
    oligo = await f.client.post(
        "/api/v1/registry/oligos",
        json={
            "name": "Visible primer",
            "sequence": unique_dna(),
            "visibility": "organization",
        },
    )
    assert oligo.status_code == 201
    target = await f.client.post(
        "/api/v1/registry/targets",
        json={
            "name": "Visible target",
            "visibility": "organization",
        },
    )
    assert target.status_code == 201
    return {
        "name": "Assay integrity",
        "experiment_type_id": method.json()["id"],
        "visibility": "organization",
        "target_id": target.json()["id"],
        "oligos": [
            {"oligo_id": oligo.json()["oligo"]["id"], "role": "forward_primer", "label": "F"}
        ],
    }


async def persisted(f: WorkspaceFixture) -> tuple[Any, ...]:
    """Independent DB session proves commits and detects rejected-operation effects."""
    async with async_sessionmaker(f.session.bind)() as session:
        assays = (
            await session.execute(
                select(
                    Assay.id,
                    Assay.public_id,
                    Assay.name,
                    Assay.target_id,
                    Assay.experiment_type_id,
                    Assay.version,
                    Assay.status,
                    Assay.updated_by_id,
                )
                .where(Assay.organization_id == f.organization.id)
                .order_by(Assay.id)
            )
        ).all()
        links = (
            await session.execute(
                select(
                    AssayOligo.assay_id,
                    AssayOligo.oligo_id,
                    AssayOligo.role,
                    AssayOligo.label,
                )
                .join(Assay)
                .where(Assay.organization_id == f.organization.id)
                .order_by(
                    AssayOligo.assay_id,
                    AssayOligo.oligo_id,
                    AssayOligo.role,
                )
            )
        ).all()
        audits = (await session.execute(select(AuditEvent.id).order_by(AuditEvent.id))).all()
        return tuple(assays), tuple(links), tuple(audits)


@pytest.mark.parametrize("operation", ["create", "update"])
@pytest.mark.parametrize(
    "case,code",
    [
        ("duplicate", "duplicate_oligo_role"),
        ("method_role", "role_not_allowed_for_experiment_type"),
        ("missing_oligo", "unknown_or_inaccessible_oligo"),
        ("hidden_oligo", "unknown_or_inaccessible_oligo"),
        ("foreign_oligo", "unknown_or_inaccessible_oligo"),
        ("missing_target", "unknown_or_inaccessible_target"),
        ("hidden_target", "unknown_or_inaccessible_target"),
        ("foreign_target", "unknown_or_inaccessible_target"),
        ("inactive_method", "invalid_experiment_type"),
        ("missing_method", "invalid_experiment_type"),
        ("invalid_role", None),
    ],
)
async def test_assay_rejections_are_atomic(
    workspace_client: WorkspaceFixture,
    operation: str,
    case: str,
    code: str | None,
) -> None:
    f = workspace_client
    payload = await setup_assay(f)
    existing = await f.client.post("/api/v1/registry/assays", json=payload)
    assert existing.status_code == 201
    existing_id = existing.json()["public_id"]
    bad = {**payload, "name": "Must never persist"}
    if case == "duplicate":
        bad["oligos"] = payload["oligos"] * 2
    elif case in {"method_role", "invalid_role"}:
        bad["oligos"] = [
            {**payload["oligos"][0], "role": "probe" if case == "method_role" else "invented"}
        ]
    elif case.endswith("method"):
        if case == "missing_method":
            bad["experiment_type_id"] = str(uuid.uuid4())
        else:
            response = await f.client.patch(
                f"/api/v1/registry/experiment-types/{payload['experiment_type_id']}",
                json={"active": False},
            )
            assert response.status_code == 200
    elif case.startswith("missing"):
        if case.endswith("oligo"):
            bad["oligos"] = [{"oligo_id": str(uuid.uuid4()), "role": "forward_primer"}]
        else:
            bad["target_id"] = str(uuid.uuid4())
    else:
        entity = "oligos" if case.endswith("oligo") else "targets"
        record_payload = {"name": "Secret scientific record", "visibility": "private"}
        if entity == "oligos":
            record_payload["sequence"] = unique_dna()
        hidden = await f.client.post(f"/api/v1/registry/{entity}", json=record_payload)
        assert hidden.status_code == 201
        record = hidden.json()["oligo"] if entity == "oligos" else hidden.json()
        if case.startswith("foreign"):
            organization = Organization(name=uuid.uuid4().hex, slug=uuid.uuid4().hex)
            f.session.add(organization)
            await f.session.flush()
            obj = await f.session.get(
                Oligo if entity == "oligos" else Target, uuid.UUID(record["id"])
            )
            assert obj is not None
            obj.organization_id = organization.id
            await f.session.commit()
        if entity == "oligos":
            bad["oligos"] = [{"oligo_id": record["id"], "role": "forward_primer"}]
        else:
            bad["target_id"] = record["id"]
        # The creator is an administrator; an unrelated member cannot see the hidden reference.
    if case.startswith("hidden"):
        actor = f.admin
        actor.global_role = GlobalRole.MEMBER
        # Transfer ownership of hidden reference so the assay owner cannot read it.
        obj = await f.session.get(
            Oligo if case.endswith("oligo") else Target, uuid.UUID(record["id"])
        )
        assert obj is not None
        obj.created_by_id = f.outsider.id
        await f.session.commit()

    async def identity():
        return await _context_for_user(f.session, f.admin, development_identity=False)

    app.dependency_overrides[get_auth_context] = identity
    before = await persisted(f)
    path = "/api/v1/registry/assays"
    response = await (
        f.client.post(path, json=bad)
        if operation == "create"
        else f.client.patch(f"{path}/{existing_id}", json=bad)
    )
    assert response.status_code == 422, response.text
    if code:
        assert response.json()["detail"]["code"] == code
    assert "Secret scientific record" not in response.text
    assert await persisted(f) == before


@pytest.mark.parametrize("role", list(GlobalRole))
@pytest.mark.parametrize("relationship", ["owner", "member", "manager", "foreign"])
async def test_assay_roles_and_lifecycle_persist(
    workspace_client: WorkspaceFixture,
    role: GlobalRole,
    relationship: str,
) -> None:
    f = workspace_client
    payload = await setup_assay(f)
    project = await f.client.post("/api/v1/workspace/projects", json={"name": uuid.uuid4().hex})
    assert project.status_code == 201
    project_id = uuid.UUID(project.json()["id"])
    payload["project_id"] = str(project_id)
    # Same identity in two different valid contextual roles is permitted.
    payload["oligos"].append({**payload["oligos"][0], "role": "reverse_primer", "label": "R"})
    created = await f.client.post("/api/v1/registry/assays", json=payload)
    assert created.status_code == 201
    assay = created.json()
    actor = f.admin if relationship == "owner" else f.member
    actor.global_role = role
    if relationship in {"member", "manager"}:
        f.session.add(
            ProjectMembership(
                project_id=project_id,
                user_id=actor.id,
                role=GlobalRole.MEMBER if relationship == "member" else GlobalRole.TEAM_MANAGER,
            )
        )
    if relationship == "foreign":
        organization = Organization(name=uuid.uuid4().hex, slug=uuid.uuid4().hex)
        f.session.add(organization)
        await f.session.flush()
        actor.organization_id = organization.id
    await f.session.commit()

    async def identity():
        return await _context_for_user(f.session, actor, development_identity=False)

    app.dependency_overrides[get_auth_context] = identity
    permitted = (
        relationship != "foreign"
        and role is not GlobalRole.VIEWER
        and (relationship in {"owner", "manager"} or role is GlobalRole.ADMIN)
    )
    before = await persisted(f)
    for version, status in enumerate(["deprecated", "archived"], start=2):
        response = await f.client.patch(
            f"/api/v1/registry/assays/{assay['public_id']}", json={"status": status}
        )
        assert response.status_code == (
            200 if permitted else 404 if relationship == "foreign" else 403
        )
        if permitted:
            assert response.json()["version"] == version
            assert response.json()["public_id"] == assay["public_id"]
            saved = await persisted(f)
            assert str(saved[0][0][0]) == assay["id"]
            assert saved[0][0][5] == version
            assert saved[0][0][6].value == status
            assert len(saved[1]) == 2
            assert len(saved[2]) == len(before[2]) + version - 1
        else:
            assert await persisted(f) == before


async def test_assay_association_replacement_and_noop(workspace_client: WorkspaceFixture) -> None:
    f = workspace_client
    payload = await setup_assay(f)
    created = await f.client.post("/api/v1/registry/assays", json=payload)
    assert created.status_code == 201
    assay = created.json()
    path = f"/api/v1/registry/assays/{assay['public_id']}"
    before = await persisted(f)
    noop = await f.client.patch(path, json={"name": payload["name"], "oligos": payload["oligos"]})
    assert noop.status_code == 200
    assert noop.json()["version"] == 1
    assert await persisted(f) == before
    replacement = [{**payload["oligos"][0], "role": "reverse_primer", "label": "new label"}]
    updated = await f.client.patch(path, json={"oligos": replacement, "target_id": None})
    assert updated.status_code == 200
    saved = await persisted(f)
    assert saved[0][0][3] is None
    assert saved[0][0][5] == 2
    assert len(saved[1]) == 1
    assert saved[1][0][2].value == "reverse_primer"
    assert saved[1][0][3] == "new label"
    assert len(saved[2]) == len(before[2]) + 1
