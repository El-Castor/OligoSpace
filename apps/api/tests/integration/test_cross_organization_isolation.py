from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from test_workspace_routes import context_for, unique_dna

from oligospace_api.db.session import get_session
from oligospace_api.main import app
from oligospace_api.models.enums import GlobalRole
from oligospace_api.models.registry import AuditEvent, Organization, User
from oligospace_api.security.auth import AuthContext, get_auth_context

pytestmark = pytest.mark.skipif(
    "OLIGOSPACE_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL integration database is not configured",
)

BASE = "/api/v1"


@dataclass
class TwoOrganizations:
    client: AsyncClient
    session: AsyncSession
    current: dict[str, AuthContext] = field(default_factory=dict)
    users: dict[str, User] = field(default_factory=dict)

    def act_as(self, name: str) -> None:
        self.current["context"] = context_for(self.users[name])


@pytest.fixture
async def two_organizations(integration_database_url: str) -> AsyncIterator[TwoOrganizations]:
    engine = create_async_engine(integration_database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    unique = uuid.uuid4().hex
    async with sessions() as session:
        users: dict[str, User] = {}
        for label in ("a", "b"):
            organization = Organization(
                name=f"Isolation {label} {unique}", slug=f"isolation-{label}-{unique}", active=True
            )
            session.add(organization)
            await session.flush()
            for role in (GlobalRole.ADMIN, GlobalRole.MEMBER, GlobalRole.VIEWER):
                user = User(
                    oidc_subject=f"isolation-{label}-{role.value}-{unique}",
                    email=f"{label}-{role.value}-{unique}@integration.test",
                    display_name=f"Isolation {label} {role.value}",
                    active=True,
                    global_role=role,
                    organization_id=organization.id,
                )
                session.add(user)
                users[f"{label}_{role.value}"] = user
        await session.commit()

        state = TwoOrganizations(client=None, session=session, users=users)  # type: ignore[arg-type]

        async def session_override() -> AsyncIterator[AsyncSession]:
            yield session

        async def context_override() -> AuthContext:
            return state.current["context"]

        app.dependency_overrides[get_session] = session_override
        app.dependency_overrides[get_auth_context] = context_override
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://integration.test"
        ) as client:
            state.client = client
            yield state
        app.dependency_overrides.clear()
    await engine.dispose()


async def test_organization_a_data_is_unreachable_from_organization_b(
    two_organizations: TwoOrganizations,
) -> None:
    state = two_organizations
    client = state.client
    marker = uuid.uuid4().hex[:10]
    other_marker = uuid.uuid4().hex[:10]
    sequence = unique_dna()

    # Organization A (administrator) creates data of every ownership type, all as visible as
    # the model allows within one organization.
    state.act_as("a_admin")
    team = (await client.post(f"{BASE}/workspace/teams", json={"name": f"team-{marker}"})).json()
    project_response = await client.post(
        f"{BASE}/workspace/projects",
        json={"name": f"project-{marker}", "visibility": "organization", "team_id": team["id"]},
    )
    assert project_response.status_code == 201
    project = project_response.json()
    oligo_response = await client.post(
        f"{BASE}/registry/oligos",
        json={
            "name": f"oligo-{marker}",
            "sequence": sequence,
            "visibility": "organization",
            "owner_project_id": project["id"],
        },
    )
    assert oligo_response.status_code == 201
    oligo = oligo_response.json()["oligo"]
    target_response = await client.post(
        f"{BASE}/registry/targets",
        json={"name": f"target-{marker}", "visibility": "organization"},
    )
    assert target_response.status_code == 201
    target = target_response.json()
    a_member = state.users["a_member"]
    a_admin = state.users["a_admin"]

    # Organization B administrator: the strongest role in the wrong organization.
    state.act_as("b_admin")
    b_admin = state.users["b_admin"]
    for path in (
        f"/registry/oligos/{oligo['public_id']}",
        f"/registry/targets/{target['public_id']}",
        f"/workspace/projects/{project['public_id']}",
        f"/workspace/teams/{team['id']}",
    ):
        assert (await client.get(f"{BASE}{path}")).status_code == 404, path

    for path in (
        f"/registry/oligos?q={marker}",
        f"/registry/oligos?q={sequence}",
        f"/registry/targets?q={marker}",
        "/registry/oligos",
        "/registry/targets",
        "/workspace/projects",
        "/workspace/teams",
        "/workspace/users",
        "/workspace/admin/users",
        "/workspace/dashboard",
        f"/registry/oligos/export.csv?q={marker}",
        "/registry/oligos/export.csv",
    ):
        response = await client.get(f"{BASE}{path}")
        assert response.status_code == 200, path
        text = response.text
        for secret in (marker, sequence, a_member.email, a_admin.email, a_admin.oidc_subject):
            assert secret not in text, (path, "foreign organization data returned")

    # Modification attempts against foreign records never succeed and never change them.
    assert (
        await client.patch(
            f"{BASE}/registry/oligos/{oligo['public_id']}", json={"name": "overwritten"}
        )
    ).status_code == 404
    assert (
        await client.patch(
            f"{BASE}/registry/targets/{target['public_id']}", json={"name": "overwritten"}
        )
    ).status_code == 404
    assert (
        await client.patch(
            f"{BASE}/workspace/projects/{project['public_id']}", json={"name": "overwritten"}
        )
    ).status_code == 404
    assert (
        await client.patch(f"{BASE}/workspace/teams/{team['id']}", json={"name": "overwritten"})
    ).status_code == 404
    assert (
        await client.put(
            f"{BASE}/workspace/projects/{project['public_id']}/members/{b_admin.id}",
            json={"role": "admin"},
        )
    ).status_code == 404
    assert (
        await client.delete(
            f"{BASE}/workspace/projects/{project['public_id']}/members/{a_admin.id}"
        )
    ).status_code == 404
    assert (
        await client.put(
            f"{BASE}/workspace/teams/{team['id']}/members/{b_admin.id}", json={"role": "admin"}
        )
    ).status_code == 404
    assert (
        await client.patch(f"{BASE}/workspace/admin/users/{a_admin.id}", json={"active": False})
    ).status_code == 404
    assert (
        await client.patch(
            f"{BASE}/workspace/admin/users/{a_member.id}", json={"global_role": "admin"}
        )
    ).status_code == 404

    # Foreign keys may not point at the other organization's team, project or users.
    own_project = (
        await client.post(
            f"{BASE}/workspace/projects",
            json={"name": f"own-{other_marker}", "visibility": "organization"},
        )
    ).json()
    forbidden_writes = [
        ("/workspace/projects", {"name": f"x-{other_marker}", "team_id": team["id"]}),
        ("/registry/oligos", {"name": "x", "sequence": unique_dna(), "owner_team_id": team["id"]}),
        (
            "/registry/oligos",
            {"name": "x", "sequence": unique_dna(), "owner_project_id": project["id"]},
        ),
        ("/registry/targets", {"name": "x", "owner_project_id": project["id"]}),
    ]
    for path, payload in forbidden_writes:
        response = await client.post(f"{BASE}{path}", json=payload)
        assert response.status_code in (403, 404, 422), (path, response.status_code)
    assert (
        await client.put(
            f"{BASE}/workspace/projects/{own_project['public_id']}/members/{a_member.id}",
            json={"role": "member"},
        )
    ).status_code in (403, 404, 422)

    # The same sequence in another organization is independent and discloses no foreign match.
    duplicate = await client.post(
        f"{BASE}/registry/oligos",
        json={"name": f"other-{other_marker}", "sequence": sequence, "visibility": "private"},
    )
    assert duplicate.status_code == 201
    assert oligo["public_id"] not in duplicate.text
    assert marker not in duplicate.text

    # Nothing changed for organization A, and A still sees only its own data.
    state.act_as("a_admin")
    assert (await client.get(f"{BASE}/registry/oligos/{oligo['public_id']}")).json()[
        "name"
    ] == f"oligo-{marker}"
    assert (await client.get(f"{BASE}/workspace/projects/{project['public_id']}")).json()[
        "name"
    ] == f"project-{marker}"
    a_users = await client.get(f"{BASE}/workspace/admin/users")
    assert str(a_admin.id) in a_users.text
    assert state.users["b_admin"].email not in a_users.text
    for path in ("/registry/oligos", "/workspace/projects"):
        assert other_marker not in (await client.get(f"{BASE}{path}")).text, path

    state.act_as("a_member")
    assert (
        await client.get(f"{BASE}/registry/oligos/{oligo['public_id']}")
    ).status_code == 200  # intended same-organization visibility is unchanged

    state.act_as("b_member")
    assert (await client.get(f"{BASE}/registry/oligos/{oligo['public_id']}")).status_code == 404
    state.act_as("b_viewer")
    assert (
        await client.get(f"{BASE}/workspace/projects/{project['public_id']}")
    ).status_code == 404

    # No audit event was written for the foreign records by the rejected requests.
    foreign_actor_events = await state.session.scalar(
        select(func.count())
        .select_from(AuditEvent)
        .where(
            AuditEvent.actor_id == b_admin.id,
            AuditEvent.entity_id.in_(
                [uuid.UUID(oligo["id"]), uuid.UUID(project["id"]), uuid.UUID(team["id"])]
            ),
        )
    )
    assert foreign_actor_events == 0
