from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.db.session import get_session
from oligospace_api.models.registry import Assay, Oligo, Target
from oligospace_api.repositories.registry import visible_query
from oligospace_api.repositories.workspace import visible_projects_query
from oligospace_api.security.auth import AuthContext, get_auth_context

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


class DashboardSummary(BaseModel):
    oligos: int
    assays: int
    targets: int
    projects: int
    awaiting_validation: int | None = None
    low_stock: int | None = None


async def _count(session: AsyncSession, statement: Select[Any]) -> int:
    return int(await session.scalar(select(func.count()).select_from(statement.subquery())) or 0)


@router.get("/summary", response_model=DashboardSummary)
async def summary(
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> DashboardSummary:
    principal = context.principal
    return DashboardSummary(
        oligos=await _count(session, visible_query(Oligo, principal)),
        assays=await _count(session, visible_query(Assay, principal)),
        targets=await _count(session, visible_query(Target, principal)),
        projects=await _count(session, visible_projects_query(principal)),
    )
