from __future__ import annotations

import uuid

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.domain.permissions import Principal
from oligospace_api.models.enums import GlobalRole, Visibility
from oligospace_api.models.laboratory import Attachment, ExperimentRun, Validation


def visible_run_query(principal: Principal) -> Select[tuple[ExperimentRun]]:
    statement = select(ExperimentRun).where(
        ExperimentRun.organization_id == principal.organization_id
    )
    if principal.role is GlobalRole.ADMIN:
        return statement
    return statement.where(
        or_(
            ExperimentRun.created_by_id == principal.user_id,
            ExperimentRun.operator_id == principal.user_id,
            ExperimentRun.visibility == Visibility.ORGANIZATION,
            (ExperimentRun.visibility == Visibility.TEAM)
            & ExperimentRun.owner_team_id.in_(principal.team_ids),
            (ExperimentRun.visibility == Visibility.PROJECT)
            & ExperimentRun.project_id.in_(principal.project_ids),
        )
    )


def visible_validation_query(principal: Principal) -> Select[tuple[Validation]]:
    visible_run_ids = visible_run_query(principal).with_only_columns(ExperimentRun.id)
    from oligospace_api.models.registry import Assay
    from oligospace_api.repositories.registry import visible_query

    visible_assay_ids = visible_query(Assay, principal).with_only_columns(Assay.id)
    return select(Validation).where(
        Validation.organization_id == principal.organization_id,
        Validation.assay_id.in_(visible_assay_ids),
        or_(
            Validation.experiment_run_id.is_(None),
            Validation.experiment_run_id.in_(visible_run_ids),
        ),
    )


async def get_visible_run(
    session: AsyncSession, principal: Principal, public_id: str
) -> ExperimentRun | None:
    run: ExperimentRun | None = await session.scalar(
        visible_run_query(principal).where(ExperimentRun.public_id == public_id.upper())
    )
    return run


async def get_visible_validation(
    session: AsyncSession, principal: Principal, public_id: str
) -> Validation | None:
    validation: Validation | None = await session.scalar(
        visible_validation_query(principal).where(Validation.public_id == public_id.upper())
    )
    return validation


async def list_runs(
    session: AsyncSession,
    principal: Principal,
    *,
    limit: int,
    offset: int,
    search: str | None,
) -> tuple[list[ExperimentRun], int]:
    statement = visible_run_query(principal)
    if search:
        pattern = f"%{search.replace('%', r'\%').replace('_', r'\_')}%"
        statement = statement.where(
            or_(
                ExperimentRun.public_id.ilike(pattern, escape="\\"),
                ExperimentRun.protocol_name.ilike(pattern, escape="\\"),
                ExperimentRun.protocol_version.ilike(pattern, escape="\\"),
            )
        )
    total = int(await session.scalar(select(func.count()).select_from(statement.subquery())) or 0)
    items = list(
        (
            await session.scalars(
                statement.order_by(ExperimentRun.performed_at.desc()).limit(limit).offset(offset)
            )
        ).all()
    )
    return items, total


async def list_validations(
    session: AsyncSession,
    principal: Principal,
    *,
    limit: int,
    offset: int,
    search: str | None,
) -> tuple[list[Validation], int]:
    statement = visible_validation_query(principal)
    if search:
        pattern = f"%{search.replace('%', r'\%').replace('_', r'\_')}%"
        statement = statement.where(
            or_(
                Validation.public_id.ilike(pattern, escape="\\"),
                Validation.conclusion.ilike(pattern, escape="\\"),
            )
        )
    total = int(await session.scalar(select(func.count()).select_from(statement.subquery())) or 0)
    items = list(
        (
            await session.scalars(
                statement.order_by(Validation.validated_at.desc()).limit(limit).offset(offset)
            )
        ).all()
    )
    return items, total


async def attachments_for_run(session: AsyncSession, run_id: uuid.UUID) -> list[Attachment]:
    return list(
        (
            await session.scalars(
                select(Attachment)
                .where(Attachment.experiment_run_id == run_id)
                .order_by(Attachment.created_at.desc())
            )
        ).all()
    )


async def attachments_for_validation(
    session: AsyncSession, validation_id: uuid.UUID
) -> list[Attachment]:
    return list(
        (
            await session.scalars(
                select(Attachment)
                .where(Attachment.validation_id == validation_id)
                .order_by(Attachment.created_at.desc())
            )
        ).all()
    )
