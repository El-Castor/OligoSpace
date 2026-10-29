from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, Header, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.db.session import get_session
from oligospace_api.models.enums import ScientificJobKind, ScientificJobStatus
from oligospace_api.repositories.scientific import get_visible_job, list_visible_jobs
from oligospace_api.schemas.scientific import (
    AssayPrimer3PairJobCreate,
    OligoPrimer3JobCreate,
    ScientificJobPage,
    ScientificJobRead,
)
from oligospace_api.security.auth import AuthContext, get_auth_context
from oligospace_api.services.scientific import retry_job, submit_assay_pair, submit_oligo_qc
from oligospace_api.services.scientific_queue import ScientificQueue, get_scientific_queue

router = APIRouter(prefix="/scientific-jobs", tags=["scientific-jobs"])


@router.post("/oligo-primer3-qc", response_model=ScientificJobRead)
async def create_oligo_primer3_qc(
    payload: OligoPrimer3JobCreate,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=128),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
    queue: ScientificQueue = Depends(get_scientific_queue),
) -> ScientificJobRead:
    job, replayed = await submit_oligo_qc(
        session, context.principal, payload, idempotency_key, queue
    )
    response.status_code = status.HTTP_200_OK if replayed else status.HTTP_202_ACCEPTED
    return ScientificJobRead.model_validate(job)


@router.post("/assay-primer3-pair", response_model=ScientificJobRead)
async def create_assay_primer3_pair(
    payload: AssayPrimer3PairJobCreate,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=128),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
    queue: ScientificQueue = Depends(get_scientific_queue),
) -> ScientificJobRead:
    job, replayed = await submit_assay_pair(
        session, context.principal, payload, idempotency_key, queue
    )
    response.status_code = status.HTTP_200_OK if replayed else status.HTTP_202_ACCEPTED
    return ScientificJobRead.model_validate(job)


@router.get("", response_model=ScientificJobPage)
async def scientific_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    kind: ScientificJobKind | None = None,
    state: ScientificJobStatus | None = None,
    oligo_id: uuid.UUID | None = None,
    assay_id: uuid.UUID | None = None,
    requester_id: uuid.UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ScientificJobPage:
    items, total = await list_visible_jobs(
        session,
        context.principal,
        limit=limit,
        offset=offset,
        kind=kind,
        state=state,
        oligo_id=oligo_id,
        assay_id=assay_id,
        requester_id=requester_id,
        created_from=created_from,
        created_to=created_to,
    )
    return ScientificJobPage(
        items=[ScientificJobRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{public_id}", response_model=ScientificJobRead)
async def scientific_job_detail(
    public_id: str,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ScientificJobRead:
    job = await get_visible_job(session, context.principal, public_id)
    if job is None:
        from fastapi import HTTPException

        raise HTTPException(404, detail={"code": "not_found"})
    return ScientificJobRead.model_validate(job)


@router.post("/{public_id}/retry", response_model=ScientificJobRead)
async def retry_scientific_job(
    public_id: str,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
    queue: ScientificQueue = Depends(get_scientific_queue),
) -> ScientificJobRead:
    return ScientificJobRead.model_validate(
        await retry_job(session, context.principal, public_id, queue)
    )
