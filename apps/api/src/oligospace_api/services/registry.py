from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.domain.permissions import (
    Principal,
    ResourceScope,
    can_create,
    can_edit,
    can_manage_catalog,
    can_view,
)
from oligospace_api.models.registry import (
    Assay,
    AssayOligo,
    AuditEvent,
    ExperimentType,
    Oligo,
    Organism,
    Target,
)
from oligospace_api.repositories.registry import get_visible_by_public_id, visible_query
from oligospace_api.schemas.registry import (
    AssayCreate,
    AssayOligoCreate,
    AssayUpdate,
    ExperimentTypeCreate,
    ExperimentTypeUpdate,
    OligoCreate,
    OligoUpdate,
    OrganismCreate,
    OrganismUpdate,
    TargetCreate,
    TargetUpdate,
)
from oligospace_api.services.public_ids import allocate_public_id
from oligospace_api.services.sequence_analysis import (
    calculate_metrics,
    normalize_sequence,
    reverse_complement,
)
from oligospace_api.services.workspace import validate_resource_scope


def _require_create(principal: Principal) -> None:
    if not can_create(principal):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "This role cannot create resources."},
        )


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


def _json_value(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, list):
        return [_json_value(item) for item in value]
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _snapshot(record: Oligo | Target | Assay, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: _json_value(getattr(record, field)) for field in fields}


def _scope(record: Oligo | Target | Assay) -> ResourceScope:
    project_id = record.project_id if isinstance(record, Assay) else record.owner_project_id
    return ResourceScope(
        organization_id=record.organization_id,
        created_by_id=record.created_by_id,
        visibility=record.visibility,
        team_id=record.owner_team_id,
        project_id=project_id,
    )


def _require_edit(principal: Principal, record: Oligo | Target | Assay) -> None:
    if not can_edit(principal, _scope(record)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "This role cannot edit this resource."},
        )


def _not_found(entity_type: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "not_found", "message": f"{entity_type} was not found."},
    )


def _reject_null_required(data: dict[str, Any], fields: tuple[str, ...]) -> None:
    invalid = [field for field in fields if field in data and data[field] is None]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "required_field_cannot_be_null", "fields": invalid},
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


async def update_organism(
    session: AsyncSession,
    principal: Principal,
    organism_id: uuid.UUID,
    payload: OrganismUpdate,
) -> Organism:
    if not can_manage_catalog(principal):
        raise HTTPException(status_code=403, detail={"code": "admin_required"})
    organism = await session.get(Organism, organism_id)
    if organism is None:
        raise _not_found("Organism")
    data = payload.model_dump(exclude_unset=True)
    before = {field: getattr(organism, field) for field in data}
    for field, value in data.items():
        setattr(organism, field, value)
    if data:
        await session.flush()
        session.add(
            _audit(
                principal.user_id,
                "update",
                "organism",
                organism.id,
                before=before,
                after={field: getattr(organism, field) for field in data},
            )
        )
        await session.commit()
        await session.refresh(organism)
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


async def update_experiment_type(
    session: AsyncSession,
    principal: Principal,
    experiment_type_id: uuid.UUID,
    payload: ExperimentTypeUpdate,
) -> ExperimentType:
    if not can_manage_catalog(principal):
        raise HTTPException(status_code=403, detail={"code": "admin_required"})
    experiment_type = await session.get(ExperimentType, experiment_type_id)
    if experiment_type is None:
        raise _not_found("Experiment type")
    data = payload.model_dump(exclude_unset=True)
    if "allowed_roles" in data and data["allowed_roles"] is not None:
        data["allowed_roles"] = [role.value for role in data["allowed_roles"]]
    fields = (
        "name",
        "slug",
        "description",
        "allowed_roles",
        "required_metadata",
        "recommended_validation_fields",
        "active",
    )
    before = {field: _json_value(getattr(experiment_type, field)) for field in fields}
    for field, value in data.items():
        setattr(experiment_type, field, value)
    if data:
        await session.flush()
        session.add(
            _audit(
                principal.user_id,
                "update",
                "experiment_type",
                experiment_type.id,
                before=before,
                after={field: _json_value(getattr(experiment_type, field)) for field in fields},
            )
        )
        await session.commit()
        await session.refresh(experiment_type)
    return experiment_type


async def create_target(
    session: AsyncSession, principal: Principal, payload: TargetCreate
) -> Target:
    _require_create(principal)
    await validate_resource_scope(
        session,
        principal,
        visibility=payload.visibility,
        team_id=payload.owner_team_id,
        project_id=payload.owner_project_id,
    )
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
    await validate_resource_scope(
        session,
        principal,
        visibility=payload.visibility,
        team_id=payload.owner_team_id,
        project_id=payload.owner_project_id,
    )
    metrics = calculate_metrics(payload.sequence)
    exact = await session.scalar(
        select(Oligo).where(
            Oligo.organization_id == principal.organization_id,
            Oligo.normalized_sequence == metrics.normalized_sequence,
        )
    )
    if exact is not None:
        detail = {
            "code": "exact_duplicate_sequence",
            "message": "This sequence cannot be registered. Contact a registry administrator.",
        }
        if can_view(principal, _scope(exact)):
            detail.update(
                message="This sequence already exists in OligoSpace; reuse the existing oligo.",
                existing_public_id=exact.public_id,
            )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )
    reverse_match = await session.scalar(
        visible_query(Oligo, principal).where(
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


async def _validate_assay_references(
    session: AsyncSession,
    principal: Principal,
    *,
    experiment_type_id: uuid.UUID,
    target_id: uuid.UUID | None,
    oligos: list[AssayOligoCreate],
) -> None:
    experiment_type = await session.scalar(
        select(ExperimentType).where(
            ExperimentType.id == experiment_type_id, ExperimentType.active.is_(True)
        )
    )
    if experiment_type is None:
        raise HTTPException(status_code=422, detail={"code": "invalid_experiment_type"})
    requested_roles = {association.role.value for association in oligos}
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
    association_keys = {(item.oligo_id, item.role) for item in oligos}
    if len(association_keys) != len(oligos):
        raise HTTPException(status_code=422, detail={"code": "duplicate_oligo_role"})
    requested_oligo_ids = {association.oligo_id for association in oligos}
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
    if target_id is not None:
        target = await session.scalar(
            visible_query(Target, principal).where(Target.id == target_id)
        )
        if target is None:
            raise HTTPException(status_code=422, detail={"code": "unknown_or_inaccessible_target"})


async def create_assay(session: AsyncSession, principal: Principal, payload: AssayCreate) -> Assay:
    _require_create(principal)
    await validate_resource_scope(
        session,
        principal,
        visibility=payload.visibility,
        team_id=payload.owner_team_id,
        project_id=payload.project_id,
    )
    await _validate_assay_references(
        session,
        principal,
        experiment_type_id=payload.experiment_type_id,
        target_id=payload.target_id,
        oligos=payload.oligos,
    )

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


async def update_oligo(
    session: AsyncSession,
    principal: Principal,
    public_id: str,
    payload: OligoUpdate,
) -> Oligo:
    oligo = await get_visible_by_public_id(session, Oligo, principal, public_id)
    if oligo is None:
        raise _not_found("Oligo")
    _require_edit(principal, oligo)
    fields = (
        "name",
        "oligo_type",
        "description",
        "notes",
        "owner_team_id",
        "owner_project_id",
        "visibility",
        "status",
    )
    data = payload.model_dump(exclude_unset=True)
    _reject_null_required(data, ("name", "oligo_type", "visibility", "status"))
    if not data:
        return oligo
    await validate_resource_scope(
        session,
        principal,
        visibility=data.get("visibility", oligo.visibility),
        team_id=data.get("owner_team_id", oligo.owner_team_id),
        project_id=data.get("owner_project_id", oligo.owner_project_id),
    )
    before = _snapshot(oligo, fields)
    for field, value in data.items():
        setattr(oligo, field, value)
    oligo.updated_by_id = principal.user_id
    await session.flush()
    session.add(
        _audit(
            principal.user_id,
            "update",
            "oligo",
            oligo.id,
            before=before,
            after=_snapshot(oligo, fields),
        )
    )
    await session.commit()
    await session.refresh(oligo)
    return oligo


async def update_target(
    session: AsyncSession,
    principal: Principal,
    public_id: str,
    payload: TargetUpdate,
) -> Target:
    target = await get_visible_by_public_id(session, Target, principal, public_id)
    if target is None:
        raise _not_found("Target")
    _require_edit(principal, target)
    fields = (
        "name",
        "target_type",
        "organism_id",
        "reference_genome_id",
        "gene_identifier",
        "transcript_identifier",
        "description",
        "reference_sequence",
        "owner_team_id",
        "owner_project_id",
        "visibility",
        "status",
    )
    data = payload.model_dump(exclude_unset=True)
    _reject_null_required(data, ("name", "target_type", "visibility", "status"))
    if "reference_sequence" in data and data["reference_sequence"] is not None:
        data["reference_sequence"] = normalize_sequence(data["reference_sequence"])
    if not data:
        return target
    await validate_resource_scope(
        session,
        principal,
        visibility=data.get("visibility", target.visibility),
        team_id=data.get("owner_team_id", target.owner_team_id),
        project_id=data.get("owner_project_id", target.owner_project_id),
    )
    before = _snapshot(target, fields)
    for field, value in data.items():
        setattr(target, field, value)
    target.updated_by_id = principal.user_id
    await session.flush()
    session.add(
        _audit(
            principal.user_id,
            "update",
            "target",
            target.id,
            before=before,
            after=_snapshot(target, fields),
        )
    )
    await session.commit()
    await session.refresh(target)
    return target


async def update_assay(
    session: AsyncSession,
    principal: Principal,
    public_id: str,
    payload: AssayUpdate,
) -> Assay:
    assay = await get_visible_by_public_id(session, Assay, principal, public_id)
    if assay is None:
        raise _not_found("Assay")
    _require_edit(principal, assay)
    fields = (
        "name",
        "experiment_type_id",
        "target_id",
        "organism_id",
        "project_id",
        "owner_team_id",
        "expected_product",
        "expected_amplicon_length",
        "recommended_annealing_temperature_c",
        "protocol_notes",
        "method_metadata",
        "visibility",
        "status",
        "version",
    )
    data = payload.model_dump(exclude_unset=True, exclude={"oligos"})
    _reject_null_required(data, ("name", "experiment_type_id", "visibility", "status"))
    associations = payload.oligos if "oligos" in payload.model_fields_set else None
    if not data and associations is None:
        return assay
    await validate_resource_scope(
        session,
        principal,
        visibility=data.get("visibility", assay.visibility),
        team_id=data.get("owner_team_id", assay.owner_team_id),
        project_id=data.get("project_id", assay.project_id),
    )
    effective_experiment_type_id = data.get("experiment_type_id", assay.experiment_type_id)
    effective_target_id = data.get("target_id", assay.target_id)
    await _validate_assay_references(
        session,
        principal,
        experiment_type_id=effective_experiment_type_id,
        target_id=effective_target_id,
        oligos=associations
        if associations is not None
        else [
            AssayOligoCreate(oligo_id=item.oligo_id, role=item.role, label=item.label)
            for item in assay.oligos
        ],
    )
    before = _snapshot(assay, fields)
    before["oligos"] = [
        {"oligo_id": str(item.oligo_id), "role": item.role.value, "label": item.label}
        for item in assay.oligos
    ]
    for field, value in data.items():
        setattr(assay, field, value)
    if associations is not None:
        assay.oligos = [AssayOligo(**item.model_dump()) for item in associations]
    assay.version += 1
    assay.updated_by_id = principal.user_id
    await session.flush()
    after = _snapshot(assay, fields)
    after["oligos"] = [
        {"oligo_id": str(item.oligo_id), "role": item.role.value, "label": item.label}
        for item in assay.oligos
    ]
    session.add(
        _audit(
            principal.user_id,
            "update",
            "assay",
            assay.id,
            before=before,
            after=after,
        )
    )
    await session.commit()
    await session.refresh(assay)
    return assay
