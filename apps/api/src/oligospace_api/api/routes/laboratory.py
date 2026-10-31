from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.core.config import Settings, get_settings
from oligospace_api.db.session import get_session
from oligospace_api.models.laboratory import ExperimentRun, Validation
from oligospace_api.repositories.laboratory import (
    attachments_for_run,
    attachments_for_validation,
    get_visible_run,
    get_visible_validation,
    list_runs,
    list_validations,
)
from oligospace_api.schemas.laboratory import (
    AttachmentRead,
    ExperimentRunCreate,
    ExperimentRunDetail,
    ExperimentRunRead,
    ExperimentRunUpdate,
    Page,
    ValidationCreate,
    ValidationDetail,
    ValidationRead,
)
from oligospace_api.security.auth import AuthContext, get_auth_context
from oligospace_api.services.laboratory import (
    create_attachment,
    create_run,
    create_validation,
    remove_attachment,
    update_run,
    validations_for_run,
)
from oligospace_api.services.object_storage import ObjectStorage, get_object_storage

router = APIRouter(prefix="/laboratory", tags=["laboratory"])


@router.get("/upload-policy")
async def upload_policy(
    context: AuthContext = Depends(get_auth_context),
    settings: Settings = Depends(get_settings),
) -> dict[str, bool]:
    return {"uploads_enabled": settings.uploads_allowed}


def _missing(entity_type: str) -> HTTPException:
    return HTTPException(
        status_code=404,
        detail={"code": "not_found", "message": f"{entity_type} was not found."},
    )


@router.get("/runs", response_model=Page)
async def runs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=200),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> Page:
    items, total = await list_runs(session, context.principal, limit=limit, offset=offset, search=q)
    return Page(
        items=[ExperimentRunRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/runs", response_model=ExperimentRunRead, status_code=201)
async def add_run(
    payload: ExperimentRunCreate,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ExperimentRun:
    return await create_run(session, context.principal, payload)


@router.get("/runs/{public_id}", response_model=ExperimentRunDetail)
async def run_detail(
    public_id: str,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ExperimentRunDetail:
    run = await get_visible_run(session, context.principal, public_id)
    if run is None:
        raise _missing("Experiment run")
    validations = await validations_for_run(session, context.principal, run)
    attachments = await attachments_for_run(session, run.id)
    return ExperimentRunDetail(
        **ExperimentRunRead.model_validate(run).model_dump(),
        validations=[ValidationRead.model_validate(item) for item in validations],
        attachments=[AttachmentRead.model_validate(item) for item in attachments],
    )


@router.patch("/runs/{public_id}", response_model=ExperimentRunRead)
async def edit_run(
    payload: ExperimentRunUpdate,
    public_id: str,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ExperimentRun:
    return await update_run(session, context.principal, public_id, payload)


@router.get("/validations", response_model=Page)
async def validations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    q: str | None = Query(default=None, max_length=200),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> Page:
    items, total = await list_validations(
        session, context.principal, limit=limit, offset=offset, search=q
    )
    return Page(
        items=[ValidationRead.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/validations", response_model=ValidationRead, status_code=201)
async def add_validation(
    payload: ValidationCreate,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> Validation:
    return await create_validation(session, context.principal, payload)


@router.get("/validations/{public_id}", response_model=ValidationDetail)
async def validation_detail(
    public_id: str,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ValidationDetail:
    validation = await get_visible_validation(session, context.principal, public_id)
    if validation is None:
        raise _missing("Validation")
    attachments = await attachments_for_validation(session, validation.id)
    return ValidationDetail(
        **ValidationRead.model_validate(validation).model_dump(),
        attachments=[AttachmentRead.model_validate(item) for item in attachments],
    )


@router.post(
    "/{parent_type}/{parent_public_id}/attachments", response_model=AttachmentRead, status_code=201
)
async def upload_attachment(
    parent_type: str,
    parent_public_id: str,
    file: UploadFile = File(...),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
    storage: ObjectStorage = Depends(get_object_storage),
    settings: Settings = Depends(get_settings),
) -> AttachmentRead:
    if not settings.uploads_allowed:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "uploads_disabled",
                "message": (
                    "Evidence uploads are disabled for the pilot. Existing evidence is retained."
                ),
            },
        )
    body = await file.read(settings.attachment_max_bytes + 1)
    attachment = await create_attachment(
        session,
        context.principal,
        storage,
        parent_type=parent_type,
        parent_public_id=parent_public_id,
        filename=file.filename or "attachment",
        content_type=file.content_type or "application/octet-stream",
        body=body,
        max_bytes=settings.attachment_max_bytes,
    )
    return AttachmentRead.model_validate(attachment)


@router.delete("/attachments/{public_id}", response_model=AttachmentRead)
async def delete_attachment(
    public_id: str,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> AttachmentRead:
    return AttachmentRead.model_validate(
        await remove_attachment(session, context.principal, public_id)
    )
