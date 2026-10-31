from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from oligospace_api.db.session import get_session
from oligospace_api.domain.permissions import Principal
from oligospace_api.main import app
from oligospace_api.models.enums import GlobalRole
from oligospace_api.models.registry import (
    AuditEvent,
    Oligo,
    Organization,
    ProjectMembership,
    TeamMembership,
    User,
)
from oligospace_api.security.auth import AuthContext, _context_for_user, get_auth_context
from oligospace_api.services.sequence_analysis import reverse_complement

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


@pytest.mark.parametrize("audience", ["owner", "member", "outsider", "foreign"])
@pytest.mark.parametrize("match", ["exact", "reverse"])
@pytest.mark.parametrize("visibility", ["private", "project", "team", "organization"])
async def test_hidden_oligo_matches_do_not_disclose_identifiers(
    workspace_client: WorkspaceFixture, match: str, audience: str, visibility: str
) -> None:
    fixture = workspace_client
    sequence = unique_dna()
    payload = {"name": "Confidential primer", "sequence": sequence, "visibility": visibility}
    if visibility == "team":
        team = await fixture.client.post(
            "/api/v1/workspace/teams", json={"name": f"Match team {uuid.uuid4().hex}"}
        )
        assert team.status_code == 201
        payload["owner_team_id"] = team.json()["id"]
    if visibility == "project":
        project = await fixture.client.post(
            "/api/v1/workspace/projects", json={"name": f"Match project {uuid.uuid4().hex}"}
        )
        assert project.status_code == 201
        payload["owner_project_id"] = project.json()["id"]
    created = await fixture.client.post(
        "/api/v1/registry/oligos",
        json=payload,
    )
    assert created.status_code == 201
    hidden = created.json()["oligo"]
    actor = fixture.admin if audience == "owner" else fixture.outsider
    if audience == "member":
        if visibility == "team":
            fixture.session.add(
                TeamMembership(
                    team_id=uuid.UUID(payload["owner_team_id"]),
                    user_id=actor.id,
                    role=GlobalRole.MEMBER,
                )
            )
        if visibility == "project":
            fixture.session.add(
                ProjectMembership(
                    project_id=uuid.UUID(payload["owner_project_id"]),
                    user_id=actor.id,
                    role=GlobalRole.MEMBER,
                )
            )
    if audience == "foreign":
        organization = Organization(name=f"Match {uuid.uuid4().hex}", slug=uuid.uuid4().hex)
        fixture.session.add(organization)
        await fixture.session.flush()
        actor.organization_id = organization.id
    await fixture.session.commit()
    visible = audience != "foreign" and (
        audience == "owner"
        or visibility == "organization"
        or (audience == "member" and visibility in {"team", "project"})
    )

    async def outsider_override() -> AuthContext:
        return await _context_for_user(
            fixture.session,
            actor,
            development_identity=False,
        )

    app.dependency_overrides[get_auth_context] = outsider_override
    response = await fixture.client.post(
        "/api/v1/registry/oligos",
        json={
            "name": "Independent primer",
            "sequence": sequence if match == "exact" else reverse_complement(sequence),
            "visibility": "private",
        },
    )
    duplicate = match == "exact" and audience != "foreign"
    assert response.status_code == (409 if duplicate else 201)
    # Check persisted effects, including organization-scoped uniqueness.
    count = await fixture.session.scalar(
        select(func.count()).select_from(Oligo).where(Oligo.created_by_id == actor.id)
    )
    assert count == int(audience == "owner") + int(not duplicate)
    if visible:
        if match == "exact":
            assert response.json()["detail"]["existing_public_id"] == hidden["public_id"]
        else:
            assert response.json()["warnings"] == [
                f"Reverse-complement match exists: {hidden['public_id']}."
            ]
        return
    assert hidden["public_id"] not in response.text
    assert hidden["id"] not in response.text
    assert hidden["name"] not in response.text
    if duplicate:
        assert "existing_public_id" not in response.json()["detail"]
    else:
        assert response.json()["warnings"] == []


@pytest.mark.parametrize("entity", ["oligos", "targets", "assays"])
@pytest.mark.parametrize("role", list(GlobalRole))
@pytest.mark.parametrize("audience", ["owner", "team", "project", "both", "outsider", "foreign"])
async def test_registry_visibility_matrix(
    workspace_client: WorkspaceFixture, entity: str, role: GlobalRole, audience: str
) -> None:
    """Four scopes × roles × memberships, using real membership projection.

    The same list feeds association selectors and global search. A global team
    manager has no implicit membership of another team or project.
    """
    fixture = workspace_client
    client = fixture.client
    marker = f"matrix-{uuid.uuid4().hex}"
    team = await client.post("/api/v1/workspace/teams", json={"name": marker})
    assert team.status_code == 201
    team_id = uuid.UUID(team.json()["id"])
    project = await client.post(
        "/api/v1/workspace/projects",
        json={"name": marker, "team_id": str(team_id), "visibility": "private"},
    )
    assert project.status_code == 201
    project_id = uuid.UUID(project.json()["id"])
    method = None
    if entity == "assays":
        method_response = await client.post(
            "/api/v1/registry/experiment-types",
            json={"name": marker, "slug": marker, "allowed_roles": []},
        )
        assert method_response.status_code == 201
        method = method_response.json()["id"]

    records = {}
    for visibility in ("private", "project", "team", "organization"):
        payload = {"name": f"{marker}-{visibility}", "visibility": visibility}
        if entity == "oligos":
            payload["sequence"] = unique_dna()
        if entity == "targets":
            payload["gene_identifier"] = f"gene-{marker}-{visibility}"
        if method is not None:
            payload["experiment_type_id"] = method
            payload["expected_product"] = f"product-{marker}-{visibility}"
        if visibility == "team":
            payload["owner_team_id"] = str(team_id)
        if visibility == "project":
            payload["project_id" if entity == "assays" else "owner_project_id"] = str(project_id)
        response = await client.post(f"/api/v1/registry/{entity}", json=payload)
        assert response.status_code == 201, response.text
        records[visibility] = response.json()["oligo"] if entity == "oligos" else response.json()

    actor = fixture.admin if audience == "owner" else fixture.outsider
    if audience == "foreign":
        organization = Organization(name=marker, slug=marker, active=True)
        fixture.session.add(organization)
        await fixture.session.flush()
        actor.organization_id = organization.id
    actor.global_role = role
    if audience in {"team", "both"}:
        fixture.session.add(TeamMembership(team_id=team_id, user_id=actor.id, role=role))
    if audience in {"project", "both"}:
        fixture.session.add(ProjectMembership(project_id=project_id, user_id=actor.id, role=role))
    await fixture.session.commit()

    async def actor_override() -> AuthContext:
        return await _context_for_user(fixture.session, actor, development_identity=False)

    app.dependency_overrides[get_auth_context] = actor_override
    expected = set()
    if audience != "foreign":
        expected.add("organization")
        if audience == "owner" or role is GlobalRole.ADMIN:
            expected.update(records)
        if audience in {"team", "both"}:
            expected.add("team")
        if audience in {"project", "both"}:
            expected.add("project")
    expected_ids = {records[scope]["public_id"] for scope in expected}

    # Unfiltered association choices and filtered global search use the same API.
    for params in ({}, {"q": marker}, {"q": marker, "limit": 1}, {"q": marker, "offset": 1}):
        response = await client.get(f"/api/v1/registry/{entity}", params=params)
        assert response.status_code == 200
        page = response.json()
        assert page["total"] == len(expected_ids)
        actual_ids = {item["public_id"] for item in page["items"]}
        assert actual_ids <= expected_ids
        assert len(actual_ids) == min(
            params.get("limit", 50), max(0, len(expected_ids) - params.get("offset", 0))
        )
    for scope, record in records.items():
        visible = scope in expected
        detail = await client.get(f"/api/v1/registry/{entity}/{record['public_id']}")
        assert detail.status_code == (200 if visible else 404)
        terms = [record["public_id"], record["name"]]
        terms.append(
            record["normalized_sequence"]
            if entity == "oligos"
            else record["gene_identifier"]
            if entity == "targets"
            else record["expected_product"]
        )
        for term in terms:
            search = await client.get(f"/api/v1/registry/{entity}", params={"q": term})
            assert search.status_code == 200
            assert search.json()["total"] == int(visible)
            assert {item["public_id"] for item in search.json()["items"]} == (
                {record["public_id"]} if visible else set()
            )
    summary = await client.get("/api/v1/dashboard/summary")
    assert summary.status_code == 200
    assert summary.json()[entity] == len(expected_ids)

    remaining = len(expected_ids)
    for scope, membership, column, scope_id in (
        ("project", ProjectMembership, ProjectMembership.project_id, project_id),
        ("team", TeamMembership, TeamMembership.team_id, team_id),
    ):
        if role is GlobalRole.ADMIN or audience not in {scope, "both"}:
            continue
        await fixture.session.execute(
            delete(membership).where(column == scope_id, membership.user_id == actor.id)
        )
        await fixture.session.commit()
        record = records[scope]
        revoked = await client.get(f"/api/v1/registry/{entity}/{record['public_id']}")
        assert revoked.status_code == 404
        remaining -= 1
        choices = await client.get(f"/api/v1/registry/{entity}")
        assert choices.json()["total"] == remaining
        search = await client.get(f"/api/v1/registry/{entity}", params={"q": record["name"]})
        assert search.json()["total"] == 0
        summary = await client.get("/api/v1/dashboard/summary")
        assert summary.json()[entity] == remaining
