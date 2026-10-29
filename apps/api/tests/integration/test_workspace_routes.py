from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from oligospace_api.db.session import get_session
from oligospace_api.domain.permissions import Principal
from oligospace_api.main import app
from oligospace_api.models.enums import GlobalRole
from oligospace_api.models.registry import AuditEvent, Organization, User
from oligospace_api.security.auth import AuthContext, _context_for_user, get_auth_context

pytestmark = pytest.mark.skipif(
    "OLIGOSPACE_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL integration database is not configured",
)


@dataclass
class WorkspaceFixture:
    client: AsyncClient
    session: AsyncSession
    organization: Organization
    admin: User
    member: User
    outsider: User


def context_for(
    user: User,
    *,
    team_roles: dict[uuid.UUID, GlobalRole] | None = None,
    project_roles: dict[uuid.UUID, GlobalRole] | None = None,
) -> AuthContext:
    teams = team_roles or {}
    projects = project_roles or {}
    return AuthContext(
        principal=Principal(
            user.id,
            user.organization_id,
            user.global_role,
            frozenset(teams),
            frozenset(projects),
            teams,
            projects,
        ),
        user=user,
        email=user.email,
        display_name=user.display_name,
        development_identity=False,
    )


def unique_dna() -> str:
    translation = str.maketrans("0123456789abcdef", "ACGTACGTACGTACGT")
    return uuid.uuid4().hex.translate(translation)


@pytest.fixture
async def workspace_client(integration_database_url: str) -> AsyncIterator[WorkspaceFixture]:
    engine = create_async_engine(integration_database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    unique = uuid.uuid4().hex
    async with sessions() as session:
        organization = Organization(
            name=f"Workspace integration {unique}",
            slug=f"workspace-integration-{unique}",
            active=True,
        )
        session.add(organization)
        await session.flush()
        admin = User(
            oidc_subject=f"workspace-admin-{unique}",
            email=f"admin-{unique}@integration.test",
            display_name="Workspace administrator",
            active=True,
            global_role=GlobalRole.ADMIN,
            organization_id=organization.id,
        )
        member = User(
            oidc_subject=f"workspace-member-{unique}",
            email=f"member-{unique}@integration.test",
            display_name="Workspace member",
            active=True,
            global_role=GlobalRole.MEMBER,
            organization_id=organization.id,
        )
        outsider = User(
            oidc_subject=f"workspace-outsider-{unique}",
            email=f"outsider-{unique}@integration.test",
            display_name="Workspace outsider",
            active=True,
            global_role=GlobalRole.MEMBER,
            organization_id=organization.id,
        )
        session.add_all([admin, member, outsider])
        await session.commit()

        async def session_override() -> AsyncIterator[AsyncSession]:
            yield session

        async def admin_override() -> AuthContext:
            return context_for(admin)

        app.dependency_overrides[get_session] = session_override
        app.dependency_overrides[get_auth_context] = admin_override
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://integration.test"
        ) as client:
            yield WorkspaceFixture(client, session, organization, admin, member, outsider)
        app.dependency_overrides.clear()
    await engine.dispose()


async def test_identity_workspace_visibility_and_audit(
    workspace_client: WorkspaceFixture,
) -> None:
    fixture = workspace_client
    client = fixture.client

    profile = await client.patch(
        "/api/v1/workspace/profile",
        json={"first_name": "Workspace", "last_name": "Admin"},
    )
    assert profile.status_code == 200
    assert profile.json()["initials"] == "WA"

    team_response = await client.post(
        "/api/v1/workspace/teams",
        json={"name": f"Integration team {uuid.uuid4().hex[:8]}"},
    )
    assert team_response.status_code == 201
    team_id = uuid.UUID(team_response.json()["id"])

    member_response = await client.put(
        f"/api/v1/workspace/teams/{team_id}/members/{fixture.member.id}",
        json={"role": "member"},
    )
    assert member_response.status_code == 200
    assert member_response.json()["member_count"] == 2

    project_response = await client.post(
        "/api/v1/workspace/projects",
        json={
            "name": f"Private integration project {uuid.uuid4().hex[:8]}",
            "team_id": str(team_id),
            "visibility": "private",
        },
    )
    assert project_response.status_code == 201
    project = project_response.json()
    project_id = uuid.UUID(project["id"])
    project_public_id = project["public_id"]

    project_member = await client.put(
        f"/api/v1/workspace/projects/{project_public_id}/members/{fixture.member.id}",
        json={"role": "member"},
    )
    assert project_member.status_code == 200
    assert project_member.json()["member_count"] == 2

    sequences = {
        visibility: unique_dna()
        for visibility in (
            "private",
            "team",
            "project",
            "organization",
        )
    }
    created: dict[str, str] = {}
    for visibility, sequence in sequences.items():
        payload: dict[str, str] = {
            "name": f"Workspace {visibility} oligo {uuid.uuid4().hex[:8]}",
            "sequence": sequence,
            "visibility": visibility,
        }
        if visibility == "team":
            payload["owner_team_id"] = str(team_id)
        if visibility == "project":
            payload["owner_project_id"] = str(project_id)
        response = await client.post("/api/v1/registry/oligos", json=payload)
        assert response.status_code == 201, response.text
        created[visibility] = response.json()["oligo"]["public_id"]

    member_context = context_for(
        fixture.member,
        team_roles={team_id: GlobalRole.MEMBER},
        project_roles={project_id: GlobalRole.MEMBER},
    )

    async def member_override() -> AuthContext:
        return member_context

    app.dependency_overrides[get_auth_context] = member_override
    member_oligos = await client.get("/api/v1/registry/oligos")
    assert member_oligos.status_code == 200
    member_ids = {item["public_id"] for item in member_oligos.json()["items"]}
    assert created["private"] not in member_ids
    assert {created["team"], created["project"], created["organization"]} <= member_ids

    member_projects = await client.get("/api/v1/workspace/projects")
    assert member_projects.status_code == 200
    assert project_public_id in {item["public_id"] for item in member_projects.json()}

    forbidden_admin = await client.post(
        "/api/v1/workspace/admin/users",
        json={
            "external_identity_id": f"forbidden-{uuid.uuid4()}",
            "email": f"forbidden-{uuid.uuid4()}@integration.test",
            "display_name": "Forbidden user",
        },
    )
    assert forbidden_admin.status_code == 403

    forbidden_team_edit = await client.patch(
        f"/api/v1/workspace/teams/{team_id}", json={"description": "Forbidden"}
    )
    assert forbidden_team_edit.status_code == 403

    async def outsider_override() -> AuthContext:
        return context_for(fixture.outsider)

    app.dependency_overrides[get_auth_context] = outsider_override
    outsider_oligos = await client.get("/api/v1/registry/oligos")
    assert outsider_oligos.status_code == 200
    outsider_ids = {item["public_id"] for item in outsider_oligos.json()["items"]}
    assert created["organization"] in outsider_ids
    assert created["private"] not in outsider_ids
    assert created["team"] not in outsider_ids
    assert created["project"] not in outsider_ids

    fixture.outsider.active = False
    await fixture.session.commit()
    with pytest.raises(HTTPException) as disabled:
        await _context_for_user(
            fixture.session,
            fixture.outsider,
            development_identity=False,
        )
    assert disabled.value.status_code == 403
    assert disabled.value.detail["code"] == "account_disabled"

    audit_count = int(
        await fixture.session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.actor_id == fixture.admin.id)
        )
        or 0
    )
    assert audit_count >= 9
