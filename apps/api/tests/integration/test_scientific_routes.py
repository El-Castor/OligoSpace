from __future__ import annotations

import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from oligospace_api.db.session import get_session
from oligospace_api.domain.permissions import Principal
from oligospace_api.main import app
from oligospace_api.models.enums import GlobalRole, ScientificJobStatus
from oligospace_api.models.registry import AuditEvent, ExperimentType, Organization, User
from oligospace_api.models.scientific import ScientificJob
from oligospace_api.security.auth import AuthContext, get_auth_context
from oligospace_api.services.scientific_queue import get_scientific_queue

pytestmark = pytest.mark.skipif(
    "OLIGOSPACE_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL integration database is not configured",
)


@dataclass
class FakeQueue:
    calls: list[tuple[str, str]] = field(default_factory=list)

    def dispatch(self, job_id: str, claim_token: str) -> str:
        self.calls.append((job_id, claim_token))
        return f"task-{len(self.calls)}"


@dataclass
class ScientificFixture:
    client: AsyncClient
    session: AsyncSession
    queue: FakeQueue
    admin: User
    viewer: User
    experiment_type: ExperimentType


def context_for(user: User) -> AuthContext:
    return AuthContext(
        principal=Principal(user.id, user.organization_id, user.global_role),
        user=user,
        email=user.email,
        display_name=user.display_name,
        development_identity=False,
    )


@pytest.fixture
async def scientific_client(integration_database_url: str) -> AsyncIterator[ScientificFixture]:
    engine = create_async_engine(integration_database_url)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    unique = uuid.uuid4().hex
    async with sessions() as session:
        organization = Organization(
            name=f"Scientific integration {unique}",
            slug=f"scientific-integration-{unique}",
            active=True,
        )
        session.add(organization)
        await session.flush()
        admin = User(
            oidc_subject=f"scientific-admin-{unique}",
            email=f"scientific-admin-{unique}@integration.test",
            display_name="Scientific administrator",
            active=True,
            global_role=GlobalRole.ADMIN,
            organization_id=organization.id,
        )
        viewer = User(
            oidc_subject=f"scientific-viewer-{unique}",
            email=f"scientific-viewer-{unique}@integration.test",
            display_name="Scientific viewer",
            active=True,
            global_role=GlobalRole.VIEWER,
            organization_id=organization.id,
        )
        experiment_type = ExperimentType(
            name=f"Scientific PCR {unique}",
            slug=f"scientific-pcr-{unique}",
            allowed_roles=["forward_primer", "reverse_primer"],
            required_metadata={},
            recommended_validation_fields={},
            active=True,
        )
        session.add_all([admin, viewer, experiment_type])
        await session.commit()
        queue = FakeQueue()

        async def session_override() -> AsyncIterator[AsyncSession]:
            yield session

        async def admin_override() -> AuthContext:
            return context_for(admin)

        app.dependency_overrides[get_session] = session_override
        app.dependency_overrides[get_auth_context] = admin_override
        app.dependency_overrides[get_scientific_queue] = lambda: queue
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://integration.test"
        ) as client:
            yield ScientificFixture(client, session, queue, admin, viewer, experiment_type)
        app.dependency_overrides.clear()
    await engine.dispose()


async def create_oligo(
    client: AsyncClient, name: str, sequence: str, visibility: str = "organization"
) -> dict[str, object]:
    response = await client.post(
        "/api/v1/registry/oligos",
        json={"name": name, "sequence": sequence, "visibility": visibility},
    )
    assert response.status_code == 201, response.text
    return response.json()["oligo"]


async def test_persistent_jobs_idempotency_pair_roles_rbac_and_audit(
    scientific_client: ScientificFixture,
) -> None:
    fixture = scientific_client
    forward = await create_oligo(fixture.client, "Scientific forward", "ATGCGTACGTTAGCGTACGA")
    reverse = await create_oligo(fixture.client, "Scientific reverse", "TCGTACGCTAACGTACGCAT")

    first = await fixture.client.post(
        "/api/v1/scientific-jobs/oligo-primer3-qc",
        headers={"Idempotency-Key": "integration-oligo-qc"},
        json={"oligo_public_id": forward["public_id"]},
    )
    assert first.status_code == 202, first.text
    first_job = first.json()
    assert first_job["state"] == "queued"
    assert first_job["input_snapshot"]["sequence"]["sha256"]
    assert first_job["effective_parameters"]["tm_method"] == "santalucia_1998"

    replay = await fixture.client.post(
        "/api/v1/scientific-jobs/oligo-primer3-qc",
        headers={"Idempotency-Key": "integration-oligo-qc"},
        json={"oligo_public_id": forward["public_id"]},
    )
    assert replay.status_code == 200
    assert replay.json()["public_id"] == first_job["public_id"]
    assert len(fixture.queue.calls) == 1

    assay_response = await fixture.client.post(
        "/api/v1/registry/assays",
        json={
            "name": "Scientific pair assay",
            "experiment_type_id": str(fixture.experiment_type.id),
            "visibility": "organization",
            "oligos": [
                {"oligo_id": forward["id"], "role": "forward_primer"},
                {"oligo_id": reverse["id"], "role": "reverse_primer"},
            ],
        },
    )
    assert assay_response.status_code == 201, assay_response.text
    assay = assay_response.json()
    pair = await fixture.client.post(
        "/api/v1/scientific-jobs/assay-primer3-pair",
        json={"assay_public_id": assay["public_id"]},
    )
    assert pair.status_code == 202, pair.text
    pair_job = pair.json()
    assert pair_job["assay_version"] == 1
    assert (
        pair_job["input_snapshot"]["reverse"]["normalized_sequence"]
        == reverse["normalized_sequence"]
    )
    assert len(fixture.queue.calls) == 2

    invalid_pair = await fixture.client.post(
        "/api/v1/scientific-jobs/assay-primer3-pair",
        json={
            "assay_public_id": assay["public_id"],
            "forward_oligo_id": reverse["id"],
            "reverse_oligo_id": forward["id"],
        },
    )
    assert invalid_pair.status_code == 422
    assert invalid_pair.json()["detail"]["code"] == "invalid_assay_pair_roles"

    await fixture.session.commit()
    assert (
        int(await fixture.session.scalar(select(func.count()).select_from(ScientificJob)) or 0) == 2
    )
    submits = int(
        await fixture.session.scalar(
            select(func.count())
            .select_from(AuditEvent)
            .where(AuditEvent.entity_type == "scientific_job", AuditEvent.action == "submit")
        )
        or 0
    )
    assert submits == 2

    # API submission and explicit retry must carry request correlation, without
    # copying the broker claim credential into the audit payload.
    job = await fixture.session.get(ScientificJob, uuid.UUID(first_job["id"]))
    assert job is not None
    job.state = ScientificJobStatus.FAILED
    job.last_error_code = "worker_lost"
    await fixture.session.commit()
    retry = await fixture.client.post(
        f"/api/v1/scientific-jobs/{first_job['public_id']}/retry",
        headers={"X-Request-ID": "scientific-retry-audit"},
    )
    assert retry.status_code == 200, retry.text
    async with async_sessionmaker(fixture.session.bind)() as audit_session:
        audit = await audit_session.scalar(
            select(AuditEvent).where(AuditEvent.entity_id == job.id, AuditEvent.action == "retry")
        )
        assert audit is not None
        assert audit.actor_id == fixture.admin.id
        assert audit.request_id == "scientific-retry-audit"
        assert audit.before == {"state": "failed"}
        assert audit.after == {"state": "queued", "attempt_count": 0}
        persisted_job = await audit_session.get(ScientificJob, job.id)
        assert persisted_job is not None
        assert persisted_job.state is ScientificJobStatus.QUEUED
        assert job.claim_token not in str(audit.after)

    async def viewer_override() -> AuthContext:
        return context_for(fixture.viewer)

    app.dependency_overrides[get_auth_context] = viewer_override
    readable = await fixture.client.get(f"/api/v1/scientific-jobs/{first_job['public_id']}")
    assert readable.status_code == 200
    forbidden = await fixture.client.post(
        "/api/v1/scientific-jobs/oligo-primer3-qc",
        json={"oligo_public_id": forward["public_id"]},
    )
    assert forbidden.status_code == 403


async def test_pair_job_hidden_when_viewer_cannot_see_pair_oligo(
    scientific_client: ScientificFixture,
) -> None:
    fixture = scientific_client
    forward = await create_oligo(fixture.client, "Visible forward", "ATGCGTACGTTAGCGTACGA")
    reverse = await create_oligo(
        fixture.client, "Private reverse", "TCGTACGCTAACGTACGCAT", visibility="private"
    )
    assay_response = await fixture.client.post(
        "/api/v1/registry/assays",
        json={
            "name": "Assay with private reverse",
            "experiment_type_id": str(fixture.experiment_type.id),
            "visibility": "organization",
            "oligos": [
                {"oligo_id": forward["id"], "role": "forward_primer"},
                {"oligo_id": reverse["id"], "role": "reverse_primer"},
            ],
        },
    )
    assert assay_response.status_code == 201, assay_response.text
    assay = assay_response.json()
    job_response = await fixture.client.post(
        "/api/v1/scientific-jobs/assay-primer3-pair",
        json={"assay_public_id": assay["public_id"]},
    )
    assert job_response.status_code == 202, job_response.text
    job = job_response.json()

    async def viewer_override() -> AuthContext:
        return context_for(fixture.viewer)

    app.dependency_overrides[get_auth_context] = viewer_override
    detail = await fixture.client.get(f"/api/v1/scientific-jobs/{job['public_id']}")
    assert detail.status_code == 404
    listing = await fixture.client.get("/api/v1/scientific-jobs")
    assert listing.status_code == 200
    assert job["public_id"] not in {item["public_id"] for item in listing.json()["items"]}


async def test_unsupported_sequence_has_explicit_unavailable_error(
    scientific_client: ScientificFixture,
) -> None:
    oligo = await create_oligo(scientific_client.client, "Ambiguous DNA", "ATGCNNNNATGC")
    response = await scientific_client.client.post(
        "/api/v1/scientific-jobs/oligo-primer3-qc",
        json={"oligo_public_id": oligo["public_id"]},
    )
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "primer3_unsupported_sequence"
