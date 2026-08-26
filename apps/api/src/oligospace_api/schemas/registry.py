from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from oligospace_api.models.enums import OligoRole, RecordStatus, Visibility


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ExperimentTypeRead(ORMModel):
    id: uuid.UUID
    name: str
    slug: str
    description: str | None
    allowed_roles: list[str]
    required_metadata: dict[str, Any]
    recommended_validation_fields: dict[str, Any]
    active: bool


class ExperimentTypeCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", max_length=80)
    description: str | None = None
    allowed_roles: list[OligoRole] = Field(default_factory=list)
    required_metadata: dict[str, Any] = Field(default_factory=dict)
    recommended_validation_fields: dict[str, Any] = Field(default_factory=dict)


class OrganismCreate(BaseModel):
    scientific_name: str = Field(min_length=2, max_length=240)
    common_name: str | None = Field(default=None, max_length=160)
    taxonomy_id: str | None = Field(default=None, max_length=32)


class OrganismRead(ORMModel):
    id: uuid.UUID
    scientific_name: str
    common_name: str | None
    taxonomy_id: str | None


class TargetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    target_type: str = Field(default="gene", max_length=40)
    organism_id: uuid.UUID | None = None
    reference_genome_id: uuid.UUID | None = None
    gene_identifier: str | None = Field(default=None, max_length=160)
    transcript_identifier: str | None = Field(default=None, max_length=160)
    description: str | None = None
    reference_sequence: str | None = None
    owner_team_id: uuid.UUID | None = None
    owner_project_id: uuid.UUID | None = None
    visibility: Visibility = Visibility.TEAM


class TargetRead(ORMModel):
    id: uuid.UUID
    public_id: str
    name: str
    target_type: str
    organism_id: uuid.UUID | None
    reference_genome_id: uuid.UUID | None
    gene_identifier: str | None
    transcript_identifier: str | None
    description: str | None
    reference_sequence: str | None
    visibility: Visibility
    status: RecordStatus
    created_at: datetime
    updated_at: datetime


class TargetUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=240)
    target_type: str | None = Field(default=None, min_length=1, max_length=40)
    organism_id: uuid.UUID | None = None
    reference_genome_id: uuid.UUID | None = None
    gene_identifier: str | None = Field(default=None, max_length=160)
    transcript_identifier: str | None = Field(default=None, max_length=160)
    description: str | None = None
    reference_sequence: str | None = None
    owner_team_id: uuid.UUID | None = None
    owner_project_id: uuid.UUID | None = None
    visibility: Visibility | None = None
    status: RecordStatus | None = None


class OligoCreate(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    sequence: str = Field(min_length=1, max_length=10000)
    oligo_type: str = Field(default="DNA", max_length=80)
    description: str | None = None
    notes: str | None = None
    owner_team_id: uuid.UUID | None = None
    owner_project_id: uuid.UUID | None = None
    visibility: Visibility = Visibility.TEAM


class OligoRead(ORMModel):
    id: uuid.UUID
    public_id: str
    name: str
    sequence: str
    normalized_sequence: str
    oligo_type: str
    sequence_length: int
    gc_percent: float | None
    melting_temperature_c: float | None
    molecular_weight_g_mol: float | None
    reverse_complement: str
    calculation_provenance: dict[str, Any]
    description: str | None
    notes: str | None
    visibility: Visibility
    status: RecordStatus
    created_at: datetime
    updated_at: datetime


class OligoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=240)
    oligo_type: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = None
    notes: str | None = None
    owner_team_id: uuid.UUID | None = None
    owner_project_id: uuid.UUID | None = None
    visibility: Visibility | None = None
    status: RecordStatus | None = None


class OligoCreateResult(BaseModel):
    oligo: OligoRead
    warnings: list[str] = Field(default_factory=list)


class AssayOligoCreate(BaseModel):
    oligo_id: uuid.UUID
    role: OligoRole
    label: str | None = Field(default=None, max_length=120)


class AssayCreate(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    experiment_type_id: uuid.UUID
    target_id: uuid.UUID | None = None
    organism_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    owner_team_id: uuid.UUID | None = None
    expected_product: str | None = None
    expected_amplicon_length: int | None = Field(default=None, gt=0)
    recommended_annealing_temperature_c: float | None = None
    protocol_notes: str | None = None
    method_metadata: dict[str, Any] = Field(default_factory=dict)
    visibility: Visibility = Visibility.TEAM
    oligos: list[AssayOligoCreate] = Field(default_factory=list)


class AssayOligoRead(ORMModel):
    oligo_id: uuid.UUID
    role: OligoRole
    label: str | None


class AssayRead(ORMModel):
    id: uuid.UUID
    public_id: str
    name: str
    experiment_type_id: uuid.UUID
    target_id: uuid.UUID | None
    organism_id: uuid.UUID | None
    project_id: uuid.UUID | None
    owner_team_id: uuid.UUID | None
    expected_product: str | None
    expected_amplicon_length: int | None
    recommended_annealing_temperature_c: float | None
    protocol_notes: str | None
    method_metadata: dict[str, Any]
    visibility: Visibility
    status: RecordStatus
    version: int
    oligos: list[AssayOligoRead]
    created_at: datetime
    updated_at: datetime


class AssayUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=240)
    experiment_type_id: uuid.UUID | None = None
    target_id: uuid.UUID | None = None
    organism_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None
    owner_team_id: uuid.UUID | None = None
    expected_product: str | None = None
    expected_amplicon_length: int | None = Field(default=None, gt=0)
    recommended_annealing_temperature_c: float | None = None
    protocol_notes: str | None = None
    method_metadata: dict[str, Any] | None = None
    visibility: Visibility | None = None
    status: RecordStatus | None = None
    oligos: list[AssayOligoCreate] | None = None


class Page(BaseModel):
    items: list[Any]
    total: int
    limit: int
    offset: int
