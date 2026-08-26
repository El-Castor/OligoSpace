from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.db.session import get_session
from oligospace_api.models.registry import Assay, ExperimentType, Oligo, Organism, Target
from oligospace_api.repositories.registry import list_visible
from oligospace_api.schemas.registry import (
    AssayCreate,
    AssayRead,
    ExperimentTypeCreate,
    ExperimentTypeRead,
    OligoCreate,
    OligoCreateResult,
    OligoRead,
    OrganismCreate,
    OrganismRead,
    Page,
    TargetCreate,
    TargetRead,
)
from oligospace_api.security.auth import AuthContext, get_auth_context
from oligospace_api.services.registry import (
    create_assay,
    create_experiment_type,
    create_oligo,
    create_organism,
    create_target,
)

router = APIRouter(prefix="/registry", tags=["registry"])


@router.get("/experiment-types", response_model=list[ExperimentTypeRead])
async def experiment_types(
    active_only: bool = True,
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[ExperimentType]:
    statement = select(ExperimentType).order_by(ExperimentType.name)
    if active_only:
        statement = statement.where(ExperimentType.active.is_(True))
    return list((await session.scalars(statement)).all())


@router.post("/experiment-types", response_model=ExperimentTypeRead, status_code=201)
async def add_experiment_type(
    payload: ExperimentTypeCreate,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ExperimentType:
    return await create_experiment_type(session, context.principal, payload)


@router.get("/organisms", response_model=list[OrganismRead])
async def organisms(
    _: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[Organism]:
    return list((await session.scalars(select(Organism).order_by(Organism.scientific_name))).all())


@router.post("/organisms", response_model=OrganismRead, status_code=201)
async def add_organism(
    payload: OrganismCreate,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> Organism:
    return await create_organism(session, context.principal, payload)


@router.get("/targets", response_model=Page)
async def targets(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> Page:
    items, total = await list_visible(
        session, Target, context.principal, limit=limit, offset=offset
    )
    return Page(
        items=[TargetRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/targets", response_model=TargetRead, status_code=201)
async def add_target(
    payload: TargetCreate,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> Target:
    return await create_target(session, context.principal, payload)


@router.get("/oligos", response_model=Page)
async def oligos(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> Page:
    items, total = await list_visible(session, Oligo, context.principal, limit=limit, offset=offset)
    return Page(
        items=[OligoRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/oligos", response_model=OligoCreateResult, status_code=201)
async def add_oligo(
    payload: OligoCreate,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> OligoCreateResult:
    oligo, warnings = await create_oligo(session, context.principal, payload)
    return OligoCreateResult(oligo=OligoRead.model_validate(oligo), warnings=warnings)


@router.get("/assays", response_model=Page)
async def assays(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> Page:
    items, total = await list_visible(session, Assay, context.principal, limit=limit, offset=offset)
    return Page(
        items=[AssayRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/assays", response_model=AssayRead, status_code=201)
async def add_assay(
    payload: AssayCreate,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> Assay:
    return await create_assay(session, context.principal, payload)
