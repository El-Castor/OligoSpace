from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from oligospace_api.domain.permissions import Principal
from oligospace_api.models.enums import GlobalRole, ScientificJobKind, ScientificJobStatus
from oligospace_api.models.registry import Assay, Oligo
from oligospace_api.models.scientific import ScientificJob
from oligospace_api.repositories.registry import visible_query


def visible_scientific_jobs(principal: Principal) -> Select[tuple[ScientificJob]]:
    statement = select(ScientificJob).where(
        ScientificJob.organization_id == principal.organization_id
    )
    if principal.role is GlobalRole.ADMIN:
        return statement
    visible_oligos = visible_query(Oligo, principal).with_only_columns(Oligo.id)
    visible_assays = visible_query(Assay, principal).with_only_columns(Assay.id)
    return statement.where(
        or_(
            ScientificJob.oligo_id.in_(visible_oligos),
            ScientificJob.assay_id.in_(visible_assays),
        )
    )


async def get_visible_job(
    session: AsyncSession, principal: Principal, public_id: str
) -> ScientificJob | None:
    job: ScientificJob | None = await session.scalar(
        visible_scientific_jobs(principal)
        .options(
            selectinload(ScientificJob.attempts),
            selectinload(ScientificJob.result),
        )
        .where(ScientificJob.public_id == public_id.upper())
    )
    return job


async def list_visible_jobs(
    session: AsyncSession,
    principal: Principal,
    *,
    limit: int,
    offset: int,
    kind: ScientificJobKind | None = None,
    state: ScientificJobStatus | None = None,
    oligo_id: uuid.UUID | None = None,
    assay_id: uuid.UUID | None = None,
    requester_id: uuid.UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
) -> tuple[list[ScientificJob], int]:
    statement = visible_scientific_jobs(principal)
    if kind is not None:
        statement = statement.where(ScientificJob.kind == kind)
    if state is not None:
        statement = statement.where(ScientificJob.state == state)
    if oligo_id is not None:
        statement = statement.where(ScientificJob.oligo_id == oligo_id)
    if assay_id is not None:
        statement = statement.where(ScientificJob.assay_id == assay_id)
    if requester_id is not None:
        statement = statement.where(ScientificJob.requester_id == requester_id)
    if created_from is not None:
        statement = statement.where(ScientificJob.created_at >= created_from)
    if created_to is not None:
        statement = statement.where(ScientificJob.created_at <= created_to)
    total = int(await session.scalar(select(func.count()).select_from(statement.subquery())) or 0)
    items = list(
        (
            await session.scalars(
                statement.options(
                    selectinload(ScientificJob.attempts),
                    selectinload(ScientificJob.result),
                )
                .order_by(ScientificJob.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    return items, total
