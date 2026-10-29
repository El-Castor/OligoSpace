from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from oligospace_api.models.enums import (
    AttachmentPublicationStatus,
    AttachmentScanStatus,
    RecordStatus,
    ValidationStatus,
    Visibility,
)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ExperimentRunCreate(BaseModel):
    assay_id: uuid.UUID
    performed_at: datetime
    project_id: uuid.UUID | None = None
    owner_team_id: uuid.UUID | None = None
    protocol_name: str | None = Field(default=None, max_length=240)
    protocol_version: str | None = Field(default=None, max_length=120)
    conditions: dict[str, Any] = Field(default_factory=dict)
    input_metadata: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    visibility: Visibility = Visibility.PRIVATE


class ExperimentRunUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notes: str | None = None
    status: RecordStatus | None = None


class ExperimentRunRead(ORMModel):
    id: uuid.UUID
    public_id: str
    assay_id: uuid.UUID
    assay_version: int
    project_id: uuid.UUID | None
    owner_team_id: uuid.UUID | None
    operator_id: uuid.UUID
    performed_at: datetime
    protocol_name: str | None
    protocol_version: str | None
    conditions: dict[str, Any]
    input_metadata: dict[str, Any]
    notes: str | None
    visibility: Visibility
    status: RecordStatus
    created_at: datetime
    updated_at: datetime


class ValidationCreate(BaseModel):
    assay_id: uuid.UUID
    experiment_run_id: uuid.UUID | None = None
    status: Literal["pending", "passed", "failed", "inconclusive"]
    conclusion: str = Field(min_length=1, max_length=10000)
    measurements: dict[str, Any] = Field(default_factory=dict)
    notes: str | None = None
    validated_at: datetime
    supersedes_validation_public_id: str | None = Field(
        default=None, pattern=r"^[A-Za-z]{3}-[0-9]{6,}$", max_length=32
    )


class ValidationRead(ORMModel):
    id: uuid.UUID
    public_id: str
    assay_id: uuid.UUID
    experiment_run_id: uuid.UUID | None
    status: ValidationStatus
    conclusion: str
    measurements: dict[str, Any]
    notes: str | None
    validated_by_id: uuid.UUID
    validated_at: datetime
    supersedes_validation_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class AttachmentRead(ORMModel):
    id: uuid.UUID
    public_id: str
    experiment_run_id: uuid.UUID | None
    validation_id: uuid.UUID | None
    object_key: str
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    uploaded_by_id: uuid.UUID
    scan_status: AttachmentScanStatus
    publication_status: AttachmentPublicationStatus
    replaces_attachment_id: uuid.UUID | None
    removed_at: datetime | None
    removed_by_id: uuid.UUID | None
    created_at: datetime


class ExperimentRunDetail(ExperimentRunRead):
    validations: list[ValidationRead]
    attachments: list[AttachmentRead]


class ValidationDetail(ValidationRead):
    attachments: list[AttachmentRead]


class Page(BaseModel):
    items: list[Any]
    total: int
    limit: int
    offset: int
