from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import text as sql_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from oligospace_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from oligospace_api.models.enums import (
    ScientificAttemptStatus,
    ScientificJobKind,
    ScientificJobStatus,
    Visibility,
    database_enum,
)


class ScientificJob(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "scientific_jobs"
    __table_args__ = (
        UniqueConstraint("organization_id", "public_id", name="uq_scientific_jobs_org_public_id"),
        UniqueConstraint(
            "organization_id",
            "requester_id",
            "idempotency_key",
            name="uq_scientific_jobs_org_requester_idempotency",
        ),
        CheckConstraint("attempt_count >= 0", name="scientific_job_attempt_count_nonnegative"),
        CheckConstraint(
            "max_attempts BETWEEN 1 AND 10", name="scientific_job_max_attempts_bounded"
        ),
        CheckConstraint(
            "(kind = 'oligo_primer3_qc' AND oligo_id IS NOT NULL AND assay_id IS NULL "
            "AND forward_oligo_id IS NULL AND reverse_oligo_id IS NULL AND assay_version IS NULL) "
            "OR (kind = 'assay_primer3_pair_compatibility' AND oligo_id IS NULL "
            "AND assay_id IS NOT NULL AND forward_oligo_id IS NOT NULL "
            "AND reverse_oligo_id IS NOT NULL AND assay_version IS NOT NULL)",
            name="scientific_job_subject_shape",
        ),
        Index("ix_scientific_jobs_state_next_retry", "state", "next_retry_at"),
        Index("ix_scientific_jobs_execution_fingerprint", "execution_fingerprint"),
        Index(
            "uq_scientific_jobs_active_fingerprint",
            "organization_id",
            "requester_id",
            "kind",
            "execution_fingerprint",
            unique=True,
            postgresql_where=sql_text("state IN ('queued', 'running', 'retrying')"),
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), index=True
    )
    public_id: Mapped[str] = mapped_column(String(32), index=True)
    requester_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), index=True
    )
    kind: Mapped[ScientificJobKind] = mapped_column(
        database_enum(ScientificJobKind, "scientific_job_kind"), index=True
    )
    state: Mapped[ScientificJobStatus] = mapped_column(
        database_enum(ScientificJobStatus, "scientific_job_status"), index=True
    )
    visibility: Mapped[Visibility] = mapped_column(
        database_enum(Visibility, "scientific_job_visibility")
    )
    owner_team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="RESTRICT"), index=True
    )
    owner_project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id", ondelete="RESTRICT"), index=True
    )
    oligo_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("oligos.id", ondelete="RESTRICT"), index=True
    )
    assay_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("assays.id", ondelete="RESTRICT"), index=True
    )
    forward_oligo_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("oligos.id", ondelete="RESTRICT")
    )
    reverse_oligo_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("oligos.id", ondelete="RESTRICT")
    )
    assay_version: Mapped[int | None] = mapped_column(Integer)
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    input_sha256: Mapped[str] = mapped_column(String(64))
    requested_parameters: Mapped[dict[str, Any]] = mapped_column(JSONB)
    effective_parameters: Mapped[dict[str, Any]] = mapped_column(JSONB)
    parameter_schema_version: Mapped[str] = mapped_column(String(32))
    execution_fingerprint: Mapped[str] = mapped_column(String(64))
    idempotency_key: Mapped[str | None] = mapped_column(String(128))
    claim_token: Mapped[str] = mapped_column(String(36))
    celery_task_id: Mapped[str | None] = mapped_column(String(128))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_code: Mapped[str | None] = mapped_column(String(80))
    last_error_summary: Mapped[str | None] = mapped_column(Text)
    attempts: Mapped[list[ScientificJobAttempt]] = relationship(
        back_populates="job", lazy="selectin", order_by="ScientificJobAttempt.attempt_number"
    )
    result: Mapped[ScientificJobResult | None] = relationship(
        back_populates="job", lazy="selectin", uselist=False
    )


class ScientificJobAttempt(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "scientific_job_attempts"
    __table_args__ = (UniqueConstraint("job_id", "attempt_number"),)

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scientific_jobs.id", ondelete="RESTRICT"), index=True
    )
    attempt_number: Mapped[int] = mapped_column(Integer)
    state: Mapped[ScientificAttemptStatus] = mapped_column(
        database_enum(ScientificAttemptStatus, "scientific_attempt_status")
    )
    task_id: Mapped[str | None] = mapped_column(String(128))
    claim_token: Mapped[str] = mapped_column(String(36))
    claimed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    lease_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    retryable: Mapped[bool] = mapped_column(default=False)
    tool_version: Mapped[str | None] = mapped_column(String(80))
    worker_version: Mapped[str | None] = mapped_column(String(80))
    wrapper_contract_version: Mapped[str | None] = mapped_column(String(80))
    build_identity: Mapped[str | None] = mapped_column(String(255))
    exit_status: Mapped[int | None] = mapped_column(Integer)
    error_code: Mapped[str | None] = mapped_column(String(80))
    error_summary: Mapped[str | None] = mapped_column(Text)
    diagnostics: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    job: Mapped[ScientificJob] = relationship(back_populates="attempts")


class ScientificJobResult(Base):
    __tablename__ = "scientific_job_results"

    job_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("scientific_jobs.id", ondelete="RESTRICT"), primary_key=True
    )
    result_schema_version: Mapped[str] = mapped_column(String(32))
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB)
    warnings: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    algorithm: Mapped[str] = mapped_column(String(120))
    tool_version: Mapped[str] = mapped_column(String(80))
    tool_source_sha256: Mapped[str] = mapped_column(String(64))
    worker_version: Mapped[str] = mapped_column(String(80))
    wrapper_contract_version: Mapped[str] = mapped_column(String(80))
    build_identity: Mapped[str] = mapped_column(String(255))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    job: Mapped[ScientificJob] = relationship(back_populates="result")
