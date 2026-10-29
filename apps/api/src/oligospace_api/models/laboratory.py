from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from oligospace_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from oligospace_api.models.enums import (
    AttachmentPublicationStatus,
    AttachmentScanStatus,
    RecordStatus,
    ValidationStatus,
    Visibility,
    database_enum,
)


class ExperimentRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "experiment_runs"
    __table_args__ = (UniqueConstraint("organization_id", "public_id"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    public_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    assay_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assays.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assay_version: Mapped[int] = mapped_column(Integer, nullable=False)
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"), index=True)
    owner_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), index=True)
    operator_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    performed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    protocol_name: Mapped[str | None] = mapped_column(String(240))
    protocol_version: Mapped[str | None] = mapped_column(String(120))
    conditions: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    input_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[Visibility] = mapped_column(
        database_enum(Visibility, "experiment_run_visibility"),
        nullable=False,
        default=Visibility.PRIVATE,
    )
    status: Mapped[RecordStatus] = mapped_column(
        database_enum(RecordStatus, "experiment_run_status"),
        nullable=False,
        default=RecordStatus.ACTIVE,
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)


class Validation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "validations"
    __table_args__ = (UniqueConstraint("organization_id", "public_id"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    public_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    assay_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assays.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    experiment_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("experiment_runs.id", ondelete="RESTRICT"), index=True
    )
    status: Mapped[ValidationStatus] = mapped_column(
        database_enum(ValidationStatus, "validation_status"), nullable=False
    )
    conclusion: Mapped[str] = mapped_column(Text, nullable=False)
    measurements: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    notes: Mapped[str | None] = mapped_column(Text)
    validated_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    validated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True
    )
    supersedes_validation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("validations.id", ondelete="RESTRICT"), unique=True
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)


class Attachment(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "attachments"
    __table_args__ = (
        CheckConstraint(
            "num_nonnulls(experiment_run_id, validation_id) = 1",
            name="exactly_one_evidence_parent",
        ),
        UniqueConstraint("organization_id", "public_id"),
        UniqueConstraint("object_key"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    public_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    experiment_run_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("experiment_runs.id", ondelete="RESTRICT"), index=True
    )
    validation_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("validations.id", ondelete="RESTRICT"), index=True
    )
    object_key: Mapped[str] = mapped_column(String(512), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(160), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    uploaded_by_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    scan_status: Mapped[AttachmentScanStatus] = mapped_column(
        database_enum(AttachmentScanStatus, "attachment_scan_status"),
        nullable=False,
        default=AttachmentScanStatus.PENDING,
    )
    publication_status: Mapped[AttachmentPublicationStatus] = mapped_column(
        database_enum(AttachmentPublicationStatus, "attachment_publication_status"),
        nullable=False,
        default=AttachmentPublicationStatus.QUARANTINED,
    )
    replaces_attachment_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("attachments.id", ondelete="RESTRICT")
    )
    removed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    removed_by_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
