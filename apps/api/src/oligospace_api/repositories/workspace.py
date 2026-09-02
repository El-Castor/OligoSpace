from __future__ import annotations

import uuid

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.domain.permissions import Principal
from oligospace_api.models.enums import GlobalRole, Visibility
from oligospace_api.models.registry import Project, Team, User


def visible_teams_query(principal: Principal) -> Select[tuple[Team]]:
    statement = select(Team).where(Team.organization_id == principal.organization_id)
    if principal.role is GlobalRole.ADMIN:
        return statement
    return statement.where(Team.id.in_(principal.team_ids))


def visible_projects_query(principal: Principal) -> Select[tuple[Project]]:
    statement = select(Project).where(Project.organization_id == principal.organization_id)
    if principal.role is GlobalRole.ADMIN:
        return statement
    return statement.where(
        or_(
            Project.created_by_id == principal.user_id,
            Project.id.in_(principal.project_ids),
            Project.visibility == Visibility.ORGANIZATION,
            (Project.visibility == Visibility.TEAM) & Project.team_id.in_(principal.team_ids),
        )
    )


async def get_visible_team(
    session: AsyncSession, principal: Principal, team_id: uuid.UUID
) -> Team | None:
    result: Team | None = await session.scalar(
        visible_teams_query(principal).where(Team.id == team_id)
    )
    return result


async def get_visible_project(
    session: AsyncSession, principal: Principal, public_id: str
) -> Project | None:
    result: Project | None = await session.scalar(
        visible_projects_query(principal).where(Project.public_id == public_id.upper())
    )
    return result


async def list_visible_teams(
    session: AsyncSession, principal: Principal, search: str | None = None
) -> list[Team]:
    statement = visible_teams_query(principal)
    if search and search.strip():
        statement = statement.where(Team.name.ilike(f"%{search.strip()}%"))
    return list((await session.scalars(statement.order_by(Team.name).limit(200))).all())


async def list_visible_projects(
    session: AsyncSession, principal: Principal, search: str | None = None
) -> list[Project]:
    statement = visible_projects_query(principal)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(Project.public_id.ilike(pattern), Project.name.ilike(pattern))
        )
    result = await session.scalars(statement.order_by(Project.updated_at.desc()).limit(200))
    return list(result.all())


async def list_organization_users(
    session: AsyncSession, principal: Principal, search: str | None = None
) -> list[User]:
    statement = select(User).where(User.organization_id == principal.organization_id)
    if search and search.strip():
        pattern = f"%{search.strip()}%"
        statement = statement.where(
            or_(
                User.display_name.ilike(pattern),
                User.email.ilike(pattern),
                User.oidc_subject.ilike(pattern),
            )
        )
    return list((await session.scalars(statement.order_by(User.display_name).limit(500))).all())
