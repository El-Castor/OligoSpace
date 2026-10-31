from __future__ import annotations

import csv
import io
import os
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from test_workspace_routes import WorkspaceFixture, unique_dna

from oligospace_api.main import app
from oligospace_api.models.registry import AuditEvent, Oligo
from oligospace_api.security.auth import get_auth_context
from oligospace_api.services import csv_export

pytestmark = pytest.mark.skipif(
    "OLIGOSPACE_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL not configured",
)


async def test_csv_content_provenance_encoding_and_persisted_audit(
    workspace_client: WorkspaceFixture,
) -> None:
    f = workspace_client
    names = ['Bd21, "échantillon"\nfloraison', '=HYPERLINK("https://example.invalid")']
    created = []
    for index, name in enumerate(names):
        result = await f.client.post(
            "/api/v1/registry/oligos",
            json={
                "name": name,
                "sequence": unique_dna() if index == 0 else "NNNNNNNNNNNNNNNNNNNN",
                "visibility": "organization",
            },
        )
        assert result.status_code == 201
        created.append(result.json()["oligo"])
    request_id = f"csv-{uuid.uuid4()}"
    response = await f.client.get(
        "/api/v1/registry/oligos/export.csv",
        headers={"X-Request-ID": request_id},
    )
    assert response.status_code == 200
    assert response.content.startswith(b"\xef\xbb\xbf")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["content-disposition"] == 'attachment; filename="oligos.csv"'
    rows = list(csv.DictReader(io.StringIO(response.content.decode("utf-8-sig"))))
    by_id = {row["public_id"]: row for row in rows}
    assert len(rows) == 2
    assert by_id[created[0]["public_id"]]["name"] == names[0]
    assert by_id[created[1]["public_id"]]["name"] == "'" + names[1]
    for record in created:
        row = by_id[record["public_id"]]
        assert row["normalized_sequence"] == record["normalized_sequence"]
        assert row["gc_percent"] == (
            "" if record["gc_percent"] is None else str(record["gc_percent"])
        )
        assert row["tm_method"] == (record["calculation_provenance"]["tm_method"] or "")
        assert row["calculated_at"] == record["calculation_provenance"]["calculated_at"]
        assert "created_by_id" not in row
    async with async_sessionmaker(f.session.bind)() as session:
        audit = await session.scalar(select(AuditEvent).where(AuditEvent.request_id == request_id))
        assert audit is not None
        assert audit.actor_id == f.admin.id
        assert audit.action == "export"
        assert audit.occurred_at.tzinfo is not None
        assert audit.after == {"schema": "oligos-csv/v1", "row_count": 2, "search_applied": False}
        assert audit.before is None
        assert (
            len(
                (
                    await session.scalars(
                        select(Oligo).where(
                            Oligo.organization_id == f.organization.id,
                        )
                    )
                ).all()
            )
            == 2
        )
    empty = await f.client.get(
        "/api/v1/registry/oligos/export.csv", params={"q": "no-match-secret"}
    )
    assert empty.status_code == 200
    assert list(csv.DictReader(io.StringIO(empty.content.decode("utf-8-sig")))) == []
    assert empty.headers["x-export-row-count"] == "0"
    app.dependency_overrides.pop(get_auth_context)
    denied = await f.client.get("/api/v1/registry/oligos/export.csv")
    assert denied.status_code == 401


@pytest.mark.parametrize("bound", ["rows", "bytes"])
async def test_csv_bounds_refuse_without_success_audit(
    workspace_client: WorkspaceFixture,
    monkeypatch: pytest.MonkeyPatch,
    bound: str,
) -> None:
    f = workspace_client
    created = await f.client.post(
        "/api/v1/registry/oligos",
        json={
            "name": "Bound check",
            "sequence": unique_dna(),
            "visibility": "organization",
        },
    )
    assert created.status_code == 201
    monkeypatch.setattr(csv_export, "MAX_EXPORT_ROWS" if bound == "rows" else "MAX_EXPORT_BYTES", 0)
    before = set((await f.session.scalars(select(AuditEvent.id))).all())
    response = await f.client.get("/api/v1/registry/oligos/export.csv")
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "export_too_large"
    assert set((await f.session.scalars(select(AuditEvent.id))).all()) == before
