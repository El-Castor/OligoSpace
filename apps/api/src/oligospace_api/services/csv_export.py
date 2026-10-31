from __future__ import annotations

import csv
import io
import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.domain.permissions import Principal
from oligospace_api.models.registry import AuditEvent, Oligo
from oligospace_api.repositories.registry import list_visible

MAX_EXPORT_ROWS = 1000
MAX_EXPORT_BYTES = 8 * 1024 * 1024
COLUMNS = (
    "public_id",
    "name",
    "normalized_sequence",
    "oligo_type",
    "status",
    "sequence_length",
    "gc_percent",
    "melting_temperature_c",
    "molecular_weight_g_mol",
    "normalization",
    "gc_method",
    "tm_method",
    "molecular_weight_method",
    "calculated_at",
    "created_at",
    "updated_at",
)


def spreadsheet_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    # Neutralize leading whitespace/control tricks as well as formula operators.
    if text and (text[0] in "\t\r\n" or text.lstrip().startswith(("=", "+", "-", "@"))):
        return "'" + text
    return text


async def export_oligos(
    session: AsyncSession,
    principal: Principal,
    search: str | None,
) -> tuple[bytes, int]:
    items, total = await list_visible(
        session,
        Oligo,
        principal,
        limit=MAX_EXPORT_ROWS + 1,
        offset=0,
        search=search,
    )
    if total > MAX_EXPORT_ROWS or len(items) > MAX_EXPORT_ROWS:
        raise HTTPException(
            422,
            detail={
                "code": "export_too_large",
                "message": "Refine the search to at most 1000 oligos.",
            },
        )
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n", quoting=csv.QUOTE_ALL)
    writer.writerow(COLUMNS)
    for oligo in items:
        provenance = oligo.calculation_provenance
        values = [
            oligo.public_id,
            oligo.name,
            oligo.normalized_sequence,
            oligo.oligo_type,
            oligo.status.value,
            oligo.sequence_length,
            oligo.gc_percent,
            oligo.melting_temperature_c,
            oligo.molecular_weight_g_mol,
            *[provenance.get(key) for key in COLUMNS[9:14]],
            oligo.created_at.isoformat(),
            oligo.updated_at.isoformat(),
        ]
        writer.writerow([spreadsheet_cell(value) for value in values])
        if output.tell() > MAX_EXPORT_BYTES:
            raise HTTPException(422, detail={"code": "export_too_large"})
    body = output.getvalue().encode("utf-8-sig")
    if len(body) > MAX_EXPORT_BYTES:
        raise HTTPException(422, detail={"code": "export_too_large"})
    session.add(
        AuditEvent(
            occurred_at=datetime.now(UTC),
            actor_id=principal.user_id,
            action="export",
            entity_type="oligo_export",
            entity_id=uuid.uuid4(),
            after={
                "schema": "oligos-csv/v1",
                "row_count": len(items),
                "search_applied": bool(search and search.strip()),
            },
        )
    )
    await session.commit()
    return body, len(items)
