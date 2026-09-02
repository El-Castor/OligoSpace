from __future__ import annotations

import hashlib
import os
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from oligospace_api.core.config import Settings, get_settings
from oligospace_api.db.session import get_session
from oligospace_api.domain.permissions import Principal
from oligospace_api.main import app
from oligospace_api.models.enums import GlobalRole
from oligospace_api.models.laboratory import Attachment, ExperimentRun, Validation
from oligospace_api.models.registry import Assay, AuditEvent, ExperimentType, Organization, User
from oligospace_api.security.auth import AuthContext, get_auth_context
from oligospace_api.services.object_storage import get_object_storage

pytestmark = pytest.mark.skipif(
    "OLIGOSPACE_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL integration database is not configured",
)


@dataclass
class FakeObjectStorage:
    objects: dict[str, tuple[bytes, str]] = field(default_factory=dict)

    async def put(self, object_key: str, body: bytes, content_type: str) -> None:
        self.objects[object_key] = (body, content_type)


@dataclass
class LaboratoryFixture:
    client: AsyncClient
    session: AsyncSession
    storage: FakeObjectStorage
    admin: User
    viewer: User
    assay: Assay


def context_for(user: User) -> AuthContext:
    return AuthContext(
        principal=Principal(user.id, user.organization_id, user.global_role),
        user=user,
        email=user.email,
        display_name=user.display_name,
        development_identity=False,
    )


@pytest.fixture
async def laboratory_client() -> AsyncIterator[LaboratoryFixture]:
    engine = create_async_engine(os.environ["OLIGOSPACE_TEST_DATABASE_URL"])
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    unique = uuid.uuid4().hex
    async with sessions() as session:
        organization = Organization(
            name=f"Laboratory integration {unique}",
            slug=f"laboratory-integration-{unique}",
            active=True,
        )
        session.add(organization)
        await session.flush()
        admin = User(
            oidc_subject=f"laboratory-admin-{unique}",
            email=f"laboratory-admin-{unique}@integration.test",
            display_name="Laboratory administrator",
            active=True,
            global_role=GlobalRole.ADMIN,
            organization_id=organization.id,
        )
        viewer = User(
            oidc_subject=f"laboratory-viewer-{unique}",
            email=f"laboratory-viewer-{unique}@integration.test",
            display_name="Laboratory viewer",
            active=True,
            global_role=GlobalRole.VIEWER,
            organization_id=organization.id,
        )
        experiment_type = ExperimentType(
            name=f"Laboratory PCR {unique}",
            slug=f"laboratory-pcr-{unique}",
            allowed_roles=[],
            required_metadata={},
            recommended_validation_fields={"efficiency": {"type": "number"}},
            active=True,
        )
        session.add_all([admin, viewer, experiment_type])
        await session.flush()
        assay = Assay(
            organization_id=organization.id,
            public_id=f"ASY-{unique[:8].upper()}",
            name="Laboratory integration assay",
            experiment_type_id=experiment_type.id,
            visibility="organization",
            version=3,
            created_by_id=admin.id,
            updated_by_id=admin.id,
        )
        session.add(assay)
        await session.commit()

        storage = FakeObjectStorage()

        async def session_override() -> AsyncIterator[AsyncSession]:
            yield session

        async def admin_override() -> AuthContext:
            return context_for(admin)

        def storage_override() -> FakeObjectStorage:
            return storage

        app.dependency_overrides[get_session] = session_override
        app.dependency_overrides[get_auth_context] = admin_override
        app.dependency_overrides[get_object_storage] = storage_override
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://integration.test"
        ) as client:
            yield LaboratoryFixture(client, session, storage, admin, viewer, assay)
        app.dependency_overrides.clear()
    await engine.dispose()


async def test_run_validation_attachment_supersession_and_persistence(
    laboratory_client: LaboratoryFixture,
) -> None:
    fixture = laboratory_client
    client = fixture.client
    run_payload = {
        "assay_id": str(fixture.assay.id),
        "performed_at": "2026-09-02T09:30:00Z",
        "protocol_name": "PCR evidence protocol",
        "protocol_version": "2.1",
        "conditions": {"annealing_temperature_c": 61.5},
        "input_metadata": {"lot_reference": "user-provided-LOT-42"},
        "visibility": "organization",
    }
    first_run_response = await client.post("/api/v1/laboratory/runs", json=run_payload)
    assert first_run_response.status_code == 201, first_run_response.text
    first_run = first_run_response.json()
    assert first_run["assay_version"] == 3

    second_run_response = await client.post(
        "/api/v1/laboratory/runs",
        json={**run_payload, "performed_at": "2026-09-02T11:00:00Z"},
    )
    assert second_run_response.status_code == 201
    assert second_run_response.json()["public_id"] != first_run["public_id"]

    validation_response = await client.post(
        "/api/v1/laboratory/validations",
        json={
            "assay_id": str(fixture.assay.id),
            "experiment_run_id": first_run["id"],
            "status": "inconclusive",
            "conclusion": "Weak product requires repetition",
            "measurements": {"efficiency": 0.72},
            "validated_at": "2026-09-02T12:00:00Z",
        },
    )
    assert validation_response.status_code == 201, validation_response.text
    validation = validation_response.json()

    evidence = b"lane,sample,result\n1,A,weak\n"
    upload_response = await client.post(
        f"/api/v1/laboratory/validation/{validation['public_id']}/attachments",
        files={"file": ("evidence.csv", evidence, "text/csv")},
    )
    assert upload_response.status_code == 201, upload_response.text
    attachment = upload_response.json()
    assert attachment["publication_status"] == "quarantined"
    assert attachment["scan_status"] == "pending"
    assert attachment["sha256"] == hashlib.sha256(evidence).hexdigest()
    assert fixture.storage.objects[attachment["object_key"]] == (evidence, "text/csv")

    replacement_response = await client.post(
        "/api/v1/laboratory/validations",
        json={
            "assay_id": str(fixture.assay.id),
            "experiment_run_id": first_run["id"],
            "status": "passed",
            "conclusion": "Repeat evidence supports this run",
            "measurements": {"efficiency": 0.94},
            "validated_at": "2026-09-02T14:00:00Z",
            "supersedes_validation_public_id": validation["public_id"],
        },
    )
    assert replacement_response.status_code == 201, replacement_response.text

    await fixture.session.commit()
    run_detail = await client.get(f"/api/v1/laboratory/runs/{first_run['public_id']}")
    assert run_detail.status_code == 200
    persisted = run_detail.json()
    assert len(persisted["validations"]) == 2
    statuses = {item["status"] for item in persisted["validations"]}
    assert statuses == {"superseded", "passed"}

    persisted_attachment = await fixture.session.scalar(
        select(Attachment).where(Attachment.public_id == attachment["public_id"])
    )
    assert persisted_attachment is not None
    assert persisted_attachment.sha256 == hashlib.sha256(evidence).hexdigest()
    run_count = await fixture.session.scalar(select(func.count()).select_from(ExperimentRun))
    assert int(run_count or 0) == 2
    assert int(await fixture.session.scalar(select(func.count()).select_from(Validation)) or 0) == 2
    dashboard = await client.get("/api/v1/workspace/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["awaiting_validation"] == 1
    audit_actions = set((await fixture.session.scalars(select(AuditEvent.action))).all())
    assert {"create", "upload", "supersede"} <= audit_actions

    unsupported = await client.post(
        f"/api/v1/laboratory/run/{first_run['public_id']}/attachments",
        files={"file": ("payload.exe", b"MZ", "application/x-msdownload")},
    )
    assert unsupported.status_code == 415

    app.dependency_overrides[get_settings] = lambda: Settings(attachment_max_bytes=4)
    oversized = await client.post(
        f"/api/v1/laboratory/run/{first_run['public_id']}/attachments",
        files={"file": ("oversized.txt", b"12345", "text/plain")},
    )
    assert oversized.status_code == 413

    removed = await client.delete(f"/api/v1/laboratory/attachments/{attachment['public_id']}")
    assert removed.status_code == 200
    assert removed.json()["publication_status"] == "removed"
    assert removed.json()["removed_at"] is not None
    retained_attachment = await fixture.session.scalar(
        select(Attachment).where(Attachment.public_id == attachment["public_id"])
    )
    assert retained_attachment is not None
    assert retained_attachment.sha256 == hashlib.sha256(evidence).hexdigest()
    assert fixture.storage.objects[attachment["object_key"]][0] == evidence
    audit_actions = set((await fixture.session.scalars(select(AuditEvent.action))).all())
    assert "remove" in audit_actions

    async def viewer_override() -> AuthContext:
        return context_for(fixture.viewer)

    app.dependency_overrides[get_auth_context] = viewer_override
    forbidden = await client.post("/api/v1/laboratory/runs", json=run_payload)
    assert forbidden.status_code == 403
