from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.domain.permissions import Principal, can_create, can_manage_catalog
from oligospace_api.models.registry import (
    Assay,
    AssayOligo,
    AuditEvent,
    ExperimentType,
    Oligo,
    Organism,
    Target,
)
from oligospace_api.repositories.registry import visible_query
from oligospace_api.schemas.registry import (
    AssayCreate,
    ExperimentTypeCreate,
    OligoCreate,
    OrganismCreate,
    TargetCreate,
)
from oligospace_api.services.public_ids import allocate_public_id
from oligospace_api.services.sequence_analysis import (
    calculate_metrics,
    normalize_sequence,
    reverse_complement,
)


def _require_create(principal: Principal) -> None:
    if not can_create(principal):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "This role cannot create resources."},
        )


def _audit(actor_id: uuid.UUID, action: str, entity_type: str, entity_id: uuid.UUID) -> AuditEvent:
    return AuditEvent(
        occurred_at=datetime.now(UTC),
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )


async def create_organism(
    session: AsyncSession, principal: Principal, payload: OrganismCreate
) -> Organism:
    if not can_manage_catalog(principal):
        raise HTTPException(status_code=403, detail={"code": "admin_required"})
    organism = Organism(**payload.model_dump())
    session.add(organism)
    await session.flush()
    session.add(_audit(principal.user_id, "create", "organism", organism.id))
    await session.commit()
    return organism


async def create_experiment_type(
    session: AsyncSession, principal: Principal, payload: ExperimentTypeCreate
) -> ExperimentType:
    if not can_manage_catalog(principal):
        raise HTTPException(status_code=403, detail={"code": "admin_required"})
    data = payload.model_dump()
    data["allowed_roles"] = [role.value for role in payload.allowed_roles]
    experiment_type = ExperimentType(**data)
    session.add(experiment_type)
    await session.flush()
    session.add(_audit(principal.user_id, "create", "experiment_type", experiment_type.id))
    await session.commit()
    return experiment_type


async def create_target(
    session: AsyncSession, principal: Principal, payload: TargetCreate
) -> Target:
    _require_create(principal)
    data = payload.model_dump()
    if payload.reference_sequence is not None:
        data["reference_sequence"] = normalize_sequence(payload.reference_sequence)
    target = Target(
        **data,
        public_id=await allocate_public_id(session, "TGT"),
        organization_id=principal.organization_id,
        created_by_id=principal.user_id,
        updated_by_id=principal.user_id,
    )
    session.add(target)
    await session.flush()
    session.add(_audit(principal.user_id, "create", "target", target.id))
    await session.commit()
    return target


async def create_oligo(
    session: AsyncSession, principal: Principal, payload: OligoCreate
) -> tuple[Oligo, list[str]]:
    _require_create(principal)
    metrics = calculate_metrics(payload.sequence)
    exact = await session.scalar(
        select(Oligo).where(
            Oligo.organization_id == principal.organization_id,
            Oligo.normalized_sequence == metrics.normalized_sequence,
        )
    )
    if exact is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "exact_duplicate_sequence",
                "message": "This sequence already exists in OligoSpace; reuse the existing oligo.",
                "existing_public_id": exact.public_id,
            },
        )
    reverse_match = await session.scalar(
        select(Oligo).where(
            Oligo.organization_id == principal.organization_id,
            Oligo.normalized_sequence == reverse_complement(metrics.normalized_sequence),
        )
    )
    warnings = (
        [f"Reverse-complement match exists: {reverse_match.public_id}."]
        if reverse_match is not None
        else []
    )
    source = payload.model_dump(exclude={"sequence"})
    oligo = Oligo(
        **source,
        sequence=payload.sequence,
        normalized_sequence=metrics.normalized_sequence,
        sequence_length=metrics.length,
        gc_percent=metrics.gc_percent,
        melting_temperature_c=metrics.melting_temperature_c,
        molecular_weight_g_mol=metrics.molecular_weight_g_mol,
        reverse_complement=metrics.reverse_complement,
        calculation_provenance=metrics.provenance,
        public_id=await allocate_public_id(session, "OLG"),
        organization_id=principal.organization_id,
        created_by_id=principal.user_id,
        updated_by_id=principal.user_id,
    )
    session.add(oligo)
    await session.flush()
    session.add(_audit(principal.user_id, "create", "oligo", oligo.id))
    await session.commit()
    return oligo, warnings


async def create_assay(session: AsyncSession, principal: Principal, payload: AssayCreate) -> Assay:
    _require_create(principal)
    experiment_type = await session.scalar(
        select(ExperimentType).where(
            ExperimentType.id == payload.experiment_type_id, ExperimentType.active.is_(True)
        )
    )
    if experiment_type is None:
        raise HTTPException(status_code=422, detail={"code": "invalid_experiment_type"})
    requested_roles = {association.role.value for association in payload.oligos}
    allowed_roles = set(experiment_type.allowed_roles)
    invalid_roles = requested_roles - allowed_roles if allowed_roles else set()
    if invalid_roles:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "role_not_allowed_for_experiment_type",
                "invalid_roles": sorted(invalid_roles),
                "allowed_roles": sorted(allowed_roles),
            },
        )
    association_keys = {(item.oligo_id, item.role) for item in payload.oligos}
    if len(association_keys) != len(payload.oligos):
        raise HTTPException(status_code=422, detail={"code": "duplicate_oligo_role"})
    requested_oligo_ids = {association.oligo_id for association in payload.oligos}
    accessible_oligos = set(
        (
            await session.scalars(
                visible_query(Oligo, principal)
                .with_only_columns(Oligo.id)
                .where(Oligo.id.in_(requested_oligo_ids))
            )
        ).all()
    )
    if accessible_oligos != requested_oligo_ids:
        raise HTTPException(status_code=422, detail={"code": "unknown_or_inaccessible_oligo"})
    if payload.target_id is not None:
        target = await session.scalar(
            visible_query(Target, principal).where(Target.id == payload.target_id)
        )
        if target is None:
            raise HTTPException(status_code=422, detail={"code": "unknown_or_inaccessible_target"})

    data = payload.model_dump(exclude={"oligos"})
    assay = Assay(
        **data,
        public_id=await allocate_public_id(session, "ASY"),
        organization_id=principal.organization_id,
        created_by_id=principal.user_id,
        updated_by_id=principal.user_id,
    )
    assay.oligos = [AssayOligo(**item.model_dump()) for item in payload.oligos]
    session.add(assay)
    await session.flush()
    session.add(_audit(principal.user_id, "create", "assay", assay.id))
    await session.commit()
    return assay
