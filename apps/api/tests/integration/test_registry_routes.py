from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from oligospace_api.api.routes.registry import router
from oligospace_api.db.session import get_session
from oligospace_api.domain.permissions import Principal
from oligospace_api.main import app
from oligospace_api.models.enums import GlobalRole
from oligospace_api.models.registry import AuditEvent, ExperimentType, Organization, User
from oligospace_api.security.auth import AuthContext, get_auth_context

pytestmark = pytest.mark.skipif(
    "OLIGOSPACE_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL integration database is not configured",
)

ADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
VIEWER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
ORGANIZATION_ID = uuid.UUID("10000000-0000-0000-0000-000000000001")
EXPERIMENT_TYPE_ID = uuid.UUID("40000000-0000-0000-0000-000000000001")


@pytest.fixture
async def registry_client(
    integration_database_url: str,
) -> AsyncIterator[tuple[AsyncClient, AsyncSession]]:
    engine = create_async_engine(integration_database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    async with sessions() as session:
        session.add(
            Organization(
                id=ORGANIZATION_ID,
                name="Integration laboratory",
                slug="integration-laboratory",
                active=True,
            )
        )
        admin = User(
            id=ADMIN_ID,
            oidc_subject="integration-admin",
            email="admin@integration.test",
            display_name="Integration admin",
            active=True,
            global_role=GlobalRole.ADMIN,
            organization_id=ORGANIZATION_ID,
        )
        viewer_user = User(
            id=VIEWER_ID,
            oidc_subject="integration-viewer",
            email="viewer@integration.test",
            display_name="Integration viewer",
            active=True,
            global_role=GlobalRole.VIEWER,
            organization_id=ORGANIZATION_ID,
        )
        session.add_all([admin, viewer_user])
        session.add(
            ExperimentType(
                id=EXPERIMENT_TYPE_ID,
                name="Integration PCR",
                slug="integration-pcr",
                description="Integration test catalog entry",
                allowed_roles=["forward_primer"],
                required_metadata={},
                recommended_validation_fields={},
                active=True,
            )
        )
        await session.commit()

        async def session_override() -> AsyncIterator[AsyncSession]:
            yield session

        admin_context = AuthContext(
            principal=Principal(ADMIN_ID, ORGANIZATION_ID, GlobalRole.ADMIN),
            user=admin,
            email=admin.email,
            display_name=admin.display_name,
            development_identity=False,
        )

        async def auth_override() -> AuthContext:
            return admin_context

        app.dependency_overrides[get_session] = session_override
        app.dependency_overrides[get_auth_context] = auth_override
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://integration.test"
        ) as client:
            yield client, session
        app.dependency_overrides.clear()
    await engine.dispose()


async def test_registry_round_trip_authorization_and_audit(
    registry_client: tuple[AsyncClient, AsyncSession],
) -> None:
    client, session = registry_client

    oligo_response = await client.post(
        "/api/v1/registry/oligos",
        json={
            "name": "Integration forward primer",
            "sequence": "acgt acgt acgt",
            "visibility": "organization",
        },
    )
    assert oligo_response.status_code == 201
    oligo = oligo_response.json()["oligo"]
    assert oligo["normalized_sequence"] == "ACGTACGTACGT"

    duplicate = await client.post(
        "/api/v1/registry/oligos",
        json={"name": "Duplicate", "sequence": "ACGTACGTACGT"},
    )
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "exact_duplicate_sequence"

    search = await client.get("/api/v1/registry/oligos", params={"q": "acgt acgt"})
    assert search.status_code == 200
    assert search.json()["total"] == 1

    detail = await client.get(f"/api/v1/registry/oligos/{oligo['public_id'].lower()}")
    assert detail.status_code == 200
    assert detail.json()["public_id"] == oligo["public_id"]

    immutable_sequence = await client.patch(
        f"/api/v1/registry/oligos/{oligo['public_id']}", json={"sequence": "AAAA"}
    )
    assert immutable_sequence.status_code == 422

    updated = await client.patch(
        f"/api/v1/registry/oligos/{oligo['public_id']}",
        json={"name": "Audited forward primer"},
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Audited forward primer"

    target_response = await client.post(
        "/api/v1/registry/targets",
        json={
            "name": "Integration target",
            "gene_identifier": "GENE-TEST-1",
            "visibility": "organization",
        },
    )
    assert target_response.status_code == 201
    target = target_response.json()

    assay_response = await client.post(
        "/api/v1/registry/assays",
        json={
            "name": "Integration assay",
            "experiment_type_id": str(EXPERIMENT_TYPE_ID),
            "target_id": target["id"],
            "visibility": "organization",
            "oligos": [{"oligo_id": oligo["id"], "role": "forward_primer"}],
        },
    )
    assert assay_response.status_code == 201
    assay = assay_response.json()

    assay_update = await client.patch(
        f"/api/v1/registry/assays/{assay['public_id']}",
        json={"expected_amplicon_length": 142},
    )
    assert assay_update.status_code == 200
    assert assay_update.json()["version"] == 2

    viewer = AuthContext(
        principal=Principal(VIEWER_ID, ORGANIZATION_ID, GlobalRole.VIEWER),
        user=None,
        email="viewer@integration.test",
        display_name="Integration viewer",
        development_identity=False,
    )

    async def viewer_context() -> AuthContext:
        return viewer

    app.dependency_overrides[get_auth_context] = viewer_context
    forbidden = await client.patch(
        f"/api/v1/registry/oligos/{oligo['public_id']}", json={"name": "Forbidden edit"}
    )
    assert forbidden.status_code == 403
    app.dependency_overrides[get_auth_context] = lambda: AuthContext(
        principal=Principal(ADMIN_ID, ORGANIZATION_ID, GlobalRole.ADMIN),
        user=None,
        email="admin@integration.test",
        display_name="Integration admin",
        development_identity=False,
    )

    update_audits = int(
        await session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.action == "update", AuditEvent.actor_id == ADMIN_ID)
        )
        or 0
    )
    assert update_audits == 2


def test_registry_router_is_mounted() -> None:
    assert router.prefix == "/registry"
