from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.core.config import get_settings
from oligospace_api.domain.permissions import Principal, can_create
from oligospace_api.models.enums import (
    OligoRole,
    ScientificJobKind,
    ScientificJobStatus,
)
from oligospace_api.models.registry import Assay, AssayOligo, AuditEvent, Oligo
from oligospace_api.models.scientific import ScientificJob
from oligospace_api.repositories.registry import get_visible_by_public_id, visible_query
from oligospace_api.repositories.scientific import get_visible_job
from oligospace_api.schemas.scientific import (
    AssayPrimer3PairJobCreate,
    OligoPrimer3JobCreate,
    Primer3Parameters,
)
from oligospace_api.services.public_ids import allocate_public_id
from oligospace_api.services.scientific_contract import (
    PARAMETER_SCHEMA_VERSION,
    canonical_sha256,
    sequence_sha256,
    validate_sequence,
)
from oligospace_api.services.scientific_queue import ScientificQueue

_RETRYABLE_ERRORS = {
    "broker_unavailable",
    "database_unavailable",
    "tool_timeout",
    "worker_lost",
}


def _forbidden(message: str) -> HTTPException:
    return HTTPException(403, detail={"code": "forbidden", "message": message})


def _require_submit(principal: Principal) -> None:
    if not can_create(principal):
        raise _forbidden("This role cannot submit scientific jobs.")


def _parameters(value: Primer3Parameters | None) -> tuple[dict[str, Any], dict[str, Any]]:
    requested = value.model_dump(exclude_unset=True) if value is not None else {}
    effective = (value or Primer3Parameters()).model_dump()
    return requested, effective


async def _existing_idempotent(
    session: AsyncSession,
    principal: Principal,
    idempotency_key: str | None,
    fingerprint: str,
) -> ScientificJob | None:
    if idempotency_key:
        existing: ScientificJob | None = await session.scalar(
            select(ScientificJob).where(
                ScientificJob.organization_id == principal.organization_id,
                ScientificJob.requester_id == principal.user_id,
                ScientificJob.idempotency_key == idempotency_key,
            )
        )
        if existing is not None and existing.execution_fingerprint != fingerprint:
            raise HTTPException(
                409,
                detail={
                    "code": "idempotency_conflict",
                    "message": "This idempotency key was used for a different request.",
                },
            )
        return existing
    active_job: ScientificJob | None = await session.scalar(
        select(ScientificJob).where(
            ScientificJob.organization_id == principal.organization_id,
            ScientificJob.requester_id == principal.user_id,
            ScientificJob.execution_fingerprint == fingerprint,
            ScientificJob.state.in_(
                [
                    ScientificJobStatus.QUEUED,
                    ScientificJobStatus.RUNNING,
                    ScientificJobStatus.RETRYING,
                ]
            ),
        )
    )
    return active_job


async def _persist_and_dispatch(
    session: AsyncSession,
    principal: Principal,
    queue: ScientificQueue,
    *,
    kind: ScientificJobKind,
    visibility: Any,
    owner_team_id: uuid.UUID | None,
    owner_project_id: uuid.UUID | None,
    input_snapshot: dict[str, Any],
    requested_parameters: dict[str, Any],
    effective_parameters: dict[str, Any],
    idempotency_key: str | None,
    oligo_id: uuid.UUID | None = None,
    assay_id: uuid.UUID | None = None,
    forward_oligo_id: uuid.UUID | None = None,
    reverse_oligo_id: uuid.UUID | None = None,
    assay_version: int | None = None,
) -> tuple[ScientificJob, bool]:
    fingerprint_source = {
        "kind": kind.value,
        "input": input_snapshot,
        "effective_parameters": effective_parameters,
        "parameter_schema_version": PARAMETER_SCHEMA_VERSION,
    }
    fingerprint = canonical_sha256(fingerprint_source)
    existing = await _existing_idempotent(session, principal, idempotency_key, fingerprint)
    if existing is not None:
        loaded = await get_visible_job(session, principal, existing.public_id)
        assert loaded is not None
        return loaded, True

    active_states = (
        ScientificJobStatus.QUEUED,
        ScientificJobStatus.RUNNING,
        ScientificJobStatus.RETRYING,
    )
    settings = get_settings()
    organization_active = int(
        await session.scalar(
            select(func.count())
            .select_from(ScientificJob)
            .where(
                ScientificJob.organization_id == principal.organization_id,
                ScientificJob.state.in_(active_states),
            )
        )
        or 0
    )
    user_active = int(
        await session.scalar(
            select(func.count())
            .select_from(ScientificJob)
            .where(
                ScientificJob.organization_id == principal.organization_id,
                ScientificJob.requester_id == principal.user_id,
                ScientificJob.state.in_(active_states),
            )
        )
        or 0
    )
    if (
        organization_active >= settings.scientific_job_active_per_organization
        or user_active >= settings.scientific_job_active_per_user
    ):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "scientific_job_rate_limit",
                "message": "The active scientific-job limit has been reached.",
            },
        )

    now = datetime.now(UTC)
    job = ScientificJob(
        organization_id=principal.organization_id,
        public_id=await allocate_public_id(session, "SJOB"),
        requester_id=principal.user_id,
        kind=kind,
        state=ScientificJobStatus.QUEUED,
        visibility=visibility,
        owner_team_id=owner_team_id,
        owner_project_id=owner_project_id,
        oligo_id=oligo_id,
        assay_id=assay_id,
        forward_oligo_id=forward_oligo_id,
        reverse_oligo_id=reverse_oligo_id,
        assay_version=assay_version,
        input_snapshot=input_snapshot,
        input_sha256=canonical_sha256(input_snapshot),
        requested_parameters=requested_parameters,
        effective_parameters=effective_parameters,
        parameter_schema_version=PARAMETER_SCHEMA_VERSION,
        execution_fingerprint=fingerprint,
        idempotency_key=idempotency_key,
        claim_token=str(uuid.uuid4()),
        attempt_count=0,
        max_attempts=settings.scientific_job_max_attempts,
        queued_at=now,
    )
    session.add(job)
    await session.flush()
    session.add(
        AuditEvent(
            occurred_at=now,
            actor_id=principal.user_id,
            action="submit",
            entity_type="scientific_job",
            entity_id=job.id,
            after={"public_id": job.public_id, "kind": kind.value, "state": "queued"},
        )
    )
    await session.commit()
    try:
        job.celery_task_id = queue.dispatch(str(job.id), job.claim_token)
        await session.commit()
    except Exception as exc:
        job.last_error_code = "broker_unavailable"
        job.last_error_summary = "The job is persisted and awaits queue reconciliation."
        session.add(
            AuditEvent(
                occurred_at=datetime.now(UTC),
                actor_id=principal.user_id,
                action="dispatch_failed",
                entity_type="scientific_job",
                entity_id=job.id,
                before={"state": "queued"},
                after={"state": "queued", "error_code": "broker_unavailable"},
            )
        )
        await session.commit()
        raise HTTPException(
            status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "broker_dispatch_failed",
                "message": "The job was saved but could not be dispatched yet.",
                "job_public_id": job.public_id,
            },
        ) from exc
    loaded = await get_visible_job(session, principal, job.public_id)
    assert loaded is not None
    return loaded, False


async def submit_oligo_qc(
    session: AsyncSession,
    principal: Principal,
    payload: OligoPrimer3JobCreate,
    idempotency_key: str | None,
    queue: ScientificQueue,
) -> tuple[ScientificJob, bool]:
    _require_submit(principal)
    oligo = await get_visible_by_public_id(session, Oligo, principal, payload.oligo_public_id)
    if oligo is None:
        raise HTTPException(404, detail={"code": "subject_not_found"})
    requested, effective = _parameters(payload.parameters)
    validate_sequence(oligo.normalized_sequence, max_nn_length=effective["max_nn_length"])
    snapshot = {
        "subject": {
            "type": "oligo",
            "id": str(oligo.id),
            "public_id": oligo.public_id,
            "oligo_type": oligo.oligo_type,
        },
        "sequence": {
            "submitted": oligo.sequence,
            "normalized": oligo.normalized_sequence,
            "sha256": sequence_sha256(oligo.normalized_sequence),
            "orientation": "5_prime_to_3_prime",
        },
    }
    return await _persist_and_dispatch(
        session,
        principal,
        queue,
        kind=ScientificJobKind.OLIGO_PRIMER3_QC,
        visibility=oligo.visibility,
        owner_team_id=oligo.owner_team_id,
        owner_project_id=oligo.owner_project_id,
        oligo_id=oligo.id,
        input_snapshot=snapshot,
        requested_parameters=requested,
        effective_parameters=effective,
        idempotency_key=idempotency_key,
    )


async def _pair_oligos(
    session: AsyncSession,
    principal: Principal,
    assay: Assay,
    forward_id: uuid.UUID | None,
    reverse_id: uuid.UUID | None,
) -> tuple[Oligo, Oligo]:
    associations = list(
        (await session.scalars(select(AssayOligo).where(AssayOligo.assay_id == assay.id))).all()
    )
    forward_candidates = [a.oligo_id for a in associations if a.role is OligoRole.FORWARD_PRIMER]
    reverse_candidates = [a.oligo_id for a in associations if a.role is OligoRole.REVERSE_PRIMER]
    if forward_id is None:
        if len(forward_candidates) != 1:
            raise HTTPException(422, detail={"code": "ambiguous_forward_role"})
        forward_id = forward_candidates[0]
    if reverse_id is None:
        if len(reverse_candidates) != 1:
            raise HTTPException(422, detail={"code": "ambiguous_reverse_role"})
        reverse_id = reverse_candidates[0]
    if forward_id not in forward_candidates or reverse_id not in reverse_candidates:
        raise HTTPException(422, detail={"code": "invalid_assay_pair_roles"})
    records = list(
        (
            await session.scalars(
                visible_query(Oligo, principal).where(Oligo.id.in_([forward_id, reverse_id]))
            )
        ).all()
    )
    by_id = {record.id: record for record in records}
    if forward_id not in by_id or reverse_id not in by_id:
        raise HTTPException(422, detail={"code": "inaccessible_assay_pair"})
    return by_id[forward_id], by_id[reverse_id]


async def submit_assay_pair(
    session: AsyncSession,
    principal: Principal,
    payload: AssayPrimer3PairJobCreate,
    idempotency_key: str | None,
    queue: ScientificQueue,
) -> tuple[ScientificJob, bool]:
    _require_submit(principal)
    assay = await get_visible_by_public_id(session, Assay, principal, payload.assay_public_id)
    if assay is None:
        raise HTTPException(404, detail={"code": "subject_not_found"})
    requested, effective = _parameters(payload.parameters)
    forward, reverse = await _pair_oligos(
        session, principal, assay, payload.forward_oligo_id, payload.reverse_oligo_id
    )
    for oligo in (forward, reverse):
        validate_sequence(oligo.normalized_sequence, max_nn_length=effective["max_nn_length"])
    snapshot = {
        "subject": {
            "type": "assay",
            "id": str(assay.id),
            "public_id": assay.public_id,
            "version": assay.version,
        },
        "forward": {
            "oligo_id": str(forward.id),
            "public_id": forward.public_id,
            "role": OligoRole.FORWARD_PRIMER.value,
            "normalized_sequence": forward.normalized_sequence,
            "sha256": sequence_sha256(forward.normalized_sequence),
            "orientation": "5_prime_to_3_prime",
        },
        "reverse": {
            "oligo_id": str(reverse.id),
            "public_id": reverse.public_id,
            "role": OligoRole.REVERSE_PRIMER.value,
            "normalized_sequence": reverse.normalized_sequence,
            "sha256": sequence_sha256(reverse.normalized_sequence),
            "orientation": "5_prime_to_3_prime",
        },
    }
    return await _persist_and_dispatch(
        session,
        principal,
        queue,
        kind=ScientificJobKind.ASSAY_PRIMER3_PAIR_COMPATIBILITY,
        visibility=assay.visibility,
        owner_team_id=assay.owner_team_id,
        owner_project_id=assay.project_id,
        assay_id=assay.id,
        forward_oligo_id=forward.id,
        reverse_oligo_id=reverse.id,
        assay_version=assay.version,
        input_snapshot=snapshot,
        requested_parameters=requested,
        effective_parameters=effective,
        idempotency_key=idempotency_key,
    )


async def retry_job(
    session: AsyncSession,
    principal: Principal,
    public_id: str,
    queue: ScientificQueue,
) -> ScientificJob:
    _require_submit(principal)
    job = await get_visible_job(session, principal, public_id)
    if job is None:
        raise HTTPException(404, detail={"code": "not_found"})
    if job.requester_id != principal.user_id and principal.role.value != "admin":
        raise _forbidden("Only the requester or an administrator can retry this job.")
    if job.state is not ScientificJobStatus.FAILED or job.last_error_code not in _RETRYABLE_ERRORS:
        raise HTTPException(409, detail={"code": "job_not_retryable"})
    if job.attempt_count >= job.max_attempts:
        raise HTTPException(409, detail={"code": "retry_exhausted"})
    job.state = ScientificJobStatus.QUEUED
    job.claim_token = str(uuid.uuid4())
    job.queued_at = datetime.now(UTC)
    job.completed_at = None
    job.last_error_code = None
    job.last_error_summary = None
    session.add(
        AuditEvent(
            occurred_at=datetime.now(UTC),
            actor_id=principal.user_id,
            action="retry",
            entity_type="scientific_job",
            entity_id=job.id,
            before={"state": "failed"},
            after={"state": "queued", "attempt_count": job.attempt_count},
        )
    )
    await session.commit()
    job.celery_task_id = queue.dispatch(str(job.id), job.claim_token)
    await session.commit()
    loaded = await get_visible_job(session, principal, public_id)
    assert loaded is not None
    return loaded
