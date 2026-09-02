from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.domain.permissions import Principal, ResourceScope, can_create, can_edit
from oligospace_api.models.enums import (
    AttachmentPublicationStatus,
    AttachmentScanStatus,
    ValidationStatus,
)
from oligospace_api.models.laboratory import Attachment, ExperimentRun, Validation
from oligospace_api.models.registry import Assay, AuditEvent
from oligospace_api.repositories.laboratory import (
    get_visible_run,
    get_visible_validation,
    visible_validation_query,
)
from oligospace_api.repositories.registry import get_visible
from oligospace_api.schemas.laboratory import (
    ExperimentRunCreate,
    ExperimentRunUpdate,
    ValidationCreate,
)
from oligospace_api.services.object_storage import ObjectStorage
from oligospace_api.services.public_ids import allocate_public_id
from oligospace_api.services.workspace import validate_resource_scope

ALLOWED_ATTACHMENT_TYPES = frozenset(
    {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "text/csv",
        "text/plain",
        "text/tab-separated-values",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }
)


def _error(code: str, message: str, status_code: int) -> HTTPException:
    return HTTPException(status_code=status_code, detail={"code": code, "message": message})


def _audit(
    actor_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    *,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent(
        occurred_at=datetime.now(UTC),
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=before,
        after=after,
    )


def _require_create(principal: Principal) -> None:
    if not can_create(principal):
        raise _error("forbidden", "This role cannot record experimental evidence.", 403)


def _run_scope(run: ExperimentRun) -> ResourceScope:
    return ResourceScope(
        organization_id=run.organization_id,
        created_by_id=run.created_by_id,
        visibility=run.visibility,
        team_id=run.owner_team_id,
        project_id=run.project_id,
    )


def _require_run_edit(principal: Principal, run: ExperimentRun) -> None:
    if not can_edit(principal, _run_scope(run)):
        raise _error("forbidden", "This role cannot edit this experiment run.", 403)


async def create_run(
    session: AsyncSession, principal: Principal, payload: ExperimentRunCreate
) -> ExperimentRun:
    _require_create(principal)
    assay = await get_visible(session, Assay, principal, payload.assay_id)
    if assay is None:
        raise _error("unknown_or_inaccessible_assay", "Assay was not found.", 422)
    await validate_resource_scope(
        session,
        principal,
        visibility=payload.visibility,
        team_id=payload.owner_team_id,
        project_id=payload.project_id,
    )
    if payload.project_id is not None and assay.project_id not in {None, payload.project_id}:
        raise _error(
            "assay_project_mismatch",
            "The experiment run project does not match the assay project.",
            422,
        )
    run = ExperimentRun(
        **payload.model_dump(),
        public_id=await allocate_public_id(session, "RUN"),
        organization_id=principal.organization_id,
        assay_version=assay.version,
        operator_id=principal.user_id,
        created_by_id=principal.user_id,
        updated_by_id=principal.user_id,
    )
    session.add(run)
    await session.flush()
    session.add(
        _audit(
            principal.user_id,
            "create",
            "experiment_run",
            run.id,
            after={"assay_id": str(run.assay_id), "assay_version": run.assay_version},
        )
    )
    await session.commit()
    await session.refresh(run)
    return run


async def update_run(
    session: AsyncSession,
    principal: Principal,
    public_id: str,
    payload: ExperimentRunUpdate,
) -> ExperimentRun:
    run = await get_visible_run(session, principal, public_id)
    if run is None:
        raise _error("not_found", "Experiment run was not found.", 404)
    _require_run_edit(principal, run)
    data = payload.model_dump(exclude_unset=True)
    before = {
        "notes": run.notes,
        "status": run.status.value,
    }
    for field, value in data.items():
        setattr(run, field, value)
    if data:
        run.updated_by_id = principal.user_id
        await session.flush()
        session.add(
            _audit(
                principal.user_id,
                "update",
                "experiment_run",
                run.id,
                before=before,
                after={"notes": run.notes, "status": run.status.value},
            )
        )
        await session.commit()
        await session.refresh(run)
    return run


async def create_validation(
    session: AsyncSession, principal: Principal, payload: ValidationCreate
) -> Validation:
    _require_create(principal)
    assay = await get_visible(session, Assay, principal, payload.assay_id)
    if assay is None:
        raise _error("unknown_or_inaccessible_assay", "Assay was not found.", 422)
    run: ExperimentRun | None = None
    if payload.experiment_run_id is not None:
        run = await session.scalar(
            select(ExperimentRun).where(ExperimentRun.id == payload.experiment_run_id)
        )
        if run is None or await get_visible_run(session, principal, run.public_id) is None:
            raise _error("unknown_or_inaccessible_run", "Experiment run was not found.", 422)
        if run.assay_id != assay.id:
            raise _error(
                "validation_context_mismatch",
                "Validation run and assay must describe the same context.",
                422,
            )

    superseded: Validation | None = None
    if payload.supersedes_validation_public_id:
        superseded = await get_visible_validation(
            session, principal, payload.supersedes_validation_public_id
        )
        if superseded is None:
            raise _error("unknown_superseded_validation", "Prior validation was not found.", 422)
        if (
            superseded.assay_id != assay.id
            or superseded.experiment_run_id != payload.experiment_run_id
        ):
            raise _error(
                "supersession_context_mismatch",
                "A validation can only supersede evidence in the same context.",
                422,
            )
        already_superseded = await session.scalar(
            select(Validation.id).where(Validation.supersedes_validation_id == superseded.id)
        )
        if already_superseded is not None:
            raise _error(
                "validation_already_superseded",
                "The selected validation already has a replacement.",
                409,
            )

    data = payload.model_dump(exclude={"status", "supersedes_validation_public_id"})
    validation = Validation(
        **data,
        status=ValidationStatus(payload.status),
        public_id=await allocate_public_id(session, "VAL"),
        organization_id=principal.organization_id,
        validated_by_id=principal.user_id,
        created_by_id=principal.user_id,
        supersedes_validation_id=superseded.id if superseded else None,
    )
    session.add(validation)
    await session.flush()
    if superseded is not None:
        previous_status = superseded.status.value
        superseded.status = ValidationStatus.SUPERSEDED
        session.add(
            _audit(
                principal.user_id,
                "supersede",
                "validation",
                superseded.id,
                before={"status": previous_status},
                after={
                    "status": ValidationStatus.SUPERSEDED.value,
                    "replacement": validation.public_id,
                },
            )
        )
    session.add(
        _audit(
            principal.user_id,
            "create",
            "validation",
            validation.id,
            after={
                "assay_id": str(validation.assay_id),
                "experiment_run_id": str(validation.experiment_run_id)
                if validation.experiment_run_id
                else None,
                "status": validation.status.value,
            },
        )
    )
    await session.commit()
    await session.refresh(validation)
    return validation


async def validations_for_run(
    session: AsyncSession, principal: Principal, run: ExperimentRun
) -> list[Validation]:
    return list(
        (
            await session.scalars(
                visible_validation_query(principal)
                .where(Validation.experiment_run_id == run.id)
                .order_by(Validation.validated_at.desc())
            )
        ).all()
    )


async def create_attachment(
    session: AsyncSession,
    principal: Principal,
    storage: ObjectStorage,
    *,
    parent_type: str,
    parent_public_id: str,
    filename: str,
    content_type: str,
    body: bytes,
    max_bytes: int,
) -> Attachment:
    _require_create(principal)
    safe_name = Path(filename).name.strip()
    if not safe_name or safe_name in {".", ".."}:
        raise _error("invalid_attachment_name", "Attachment filename is invalid.", 422)
    if content_type not in ALLOWED_ATTACHMENT_TYPES:
        raise _error("unsupported_attachment_type", "Attachment type is not supported.", 415)
    if not body:
        raise _error("empty_attachment", "Attachment cannot be empty.", 422)
    if len(body) > max_bytes:
        raise _error("attachment_too_large", "Attachment exceeds the configured limit.", 413)

    run: ExperimentRun | None = None
    validation: Validation | None = None
    if parent_type == "run":
        run = await get_visible_run(session, principal, parent_public_id)
        if run is None:
            raise _error("not_found", "Experiment run was not found.", 404)
        _require_run_edit(principal, run)
    elif parent_type == "validation":
        validation = await get_visible_validation(session, principal, parent_public_id)
        if validation is None:
            raise _error("not_found", "Validation was not found.", 404)
    else:
        raise _error("invalid_attachment_parent", "Attachment parent is invalid.", 422)

    object_id = uuid.uuid4()
    parent_id = run.id if run else validation.id  # type: ignore[union-attr]
    object_key = f"{principal.organization_id}/{parent_type}/{parent_id}/{object_id}/{safe_name}"
    try:
        await storage.put(object_key, body, content_type)
    except Exception as exc:
        raise _error(
            "object_storage_unavailable",
            "The evidence object could not be stored; no metadata was committed.",
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ) from exc

    attachment = Attachment(
        organization_id=principal.organization_id,
        public_id=await allocate_public_id(session, "ATT"),
        experiment_run_id=run.id if run else None,
        validation_id=validation.id if validation else None,
        object_key=object_key,
        original_filename=safe_name,
        content_type=content_type,
        size_bytes=len(body),
        sha256=hashlib.sha256(body).hexdigest(),
        uploaded_by_id=principal.user_id,
        scan_status=AttachmentScanStatus.PENDING,
        publication_status=AttachmentPublicationStatus.QUARANTINED,
    )
    session.add(attachment)
    await session.flush()
    session.add(
        _audit(
            principal.user_id,
            "upload",
            "attachment",
            attachment.id,
            after={
                "parent_type": parent_type,
                "parent_id": str(parent_id),
                "filename": safe_name,
                "content_type": content_type,
                "size_bytes": len(body),
                "sha256": attachment.sha256,
                "publication_status": attachment.publication_status.value,
            },
        )
    )
    await session.commit()
    await session.refresh(attachment)
    return attachment


async def remove_attachment(
    session: AsyncSession, principal: Principal, public_id: str
) -> Attachment:
    attachment = await session.scalar(
        select(Attachment).where(
            Attachment.organization_id == principal.organization_id,
            Attachment.public_id == public_id.upper(),
        )
    )
    if attachment is None:
        raise _error("not_found", "Attachment was not found.", 404)
    if attachment.experiment_run_id:
        run = await session.get(ExperimentRun, attachment.experiment_run_id)
        if run is None or await get_visible_run(session, principal, run.public_id) is None:
            raise _error("not_found", "Attachment was not found.", 404)
        _require_run_edit(principal, run)
    else:
        validation = await session.get(Validation, attachment.validation_id)
        if (
            validation is None
            or await get_visible_validation(session, principal, validation.public_id) is None
        ):
            raise _error("not_found", "Attachment was not found.", 404)
    if attachment.publication_status is not AttachmentPublicationStatus.REMOVED:
        before = attachment.publication_status.value
        attachment.publication_status = AttachmentPublicationStatus.REMOVED
        attachment.removed_at = datetime.now(UTC)
        attachment.removed_by_id = principal.user_id
        session.add(
            _audit(
                principal.user_id,
                "remove",
                "attachment",
                attachment.id,
                before={"publication_status": before},
                after={"publication_status": AttachmentPublicationStatus.REMOVED.value},
            )
        )
        await session.commit()
        await session.refresh(attachment)
    return attachment
