from __future__ import annotations

import uuid
from typing import TypeVar

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.domain.permissions import Principal
from oligospace_api.models.enums import GlobalRole, Visibility
from oligospace_api.models.registry import Assay, Oligo, Target

ScopedModel = TypeVar("ScopedModel", Assay, Oligo, Target)


def visible_query(model: type[ScopedModel], principal: Principal) -> Select[tuple[ScopedModel]]:
    statement = select(model).where(model.organization_id == principal.organization_id)
    if principal.role is GlobalRole.ADMIN:
        return statement
    if model is Assay:
        project_column = Assay.project_id
    elif model is Oligo:
        project_column = Oligo.owner_project_id
    else:
        project_column = Target.owner_project_id
    return statement.where(
        or_(
            model.created_by_id == principal.user_id,
            model.visibility == Visibility.ORGANIZATION,
            (model.visibility == Visibility.TEAM) & model.owner_team_id.in_(principal.team_ids),
            (model.visibility == Visibility.PROJECT) & project_column.in_(principal.project_ids),
        )
    )


async def list_visible(
    session: AsyncSession,
    model: type[ScopedModel],
    principal: Principal,
    *,
    limit: int,
    offset: int,
) -> tuple[list[ScopedModel], int]:
    base = visible_query(model, principal)
    total = int(await session.scalar(select(func.count()).select_from(base.subquery())) or 0)
    items = list(
        (
            await session.scalars(
                base.order_by(model.created_at.desc()).limit(limit).offset(offset)
            )
        ).all()
    )
    return items, total


async def get_visible(
    session: AsyncSession,
    model: type[ScopedModel],
    principal: Principal,
    item_id: uuid.UUID,
) -> ScopedModel | None:
    item: ScopedModel | None = await session.scalar(
        visible_query(model, principal).where(model.id == item_id)
    )
    return item
