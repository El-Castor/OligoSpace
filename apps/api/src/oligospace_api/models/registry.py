from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Mapped, Mapper, mapped_column, relationship

from oligospace_api.core.audit import request_id_context, safe_audit_facts
from oligospace_api.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from oligospace_api.models.enums import (
    GlobalRole,
    OligoRole,
    RecordStatus,
    Visibility,
    database_enum,
)


class Organization(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    oidc_subject: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    identity_provider: Mapped[str] = mapped_column(String(80), nullable=False, default="keycloak")
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    first_name: Mapped[str | None] = mapped_column(String(120))
    last_name: Mapped[str | None] = mapped_column(String(120))
    avatar_url: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    global_role: Mapped[GlobalRole] = mapped_column(
        database_enum(GlobalRole, "global_role"), nullable=False, default=GlobalRole.MEMBER
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Team(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "teams"
    __table_args__ = (UniqueConstraint("organization_id", "name"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class TeamMembership(TimestampMixin, Base):
    __tablename__ = "team_memberships"

    team_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("teams.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[GlobalRole] = mapped_column(
        database_enum(GlobalRole, "team_role"), nullable=False, default=GlobalRole.MEMBER
    )


class Project(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("organization_id", "public_id"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    team_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("teams.id", ondelete="SET NULL"), index=True
    )
    public_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[Visibility] = mapped_column(
        database_enum(Visibility, "project_visibility"),
        nullable=False,
        default=Visibility.PRIVATE,
    )
    status: Mapped[RecordStatus] = mapped_column(
        database_enum(RecordStatus, "record_status"), nullable=False, default=RecordStatus.ACTIVE
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)


class ProjectMembership(TimestampMixin, Base):
    __tablename__ = "project_memberships"

    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    role: Mapped[GlobalRole] = mapped_column(
        database_enum(GlobalRole, "project_role"), nullable=False, default=GlobalRole.MEMBER
    )


class Organism(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "organisms"

    scientific_name: Mapped[str] = mapped_column(String(240), nullable=False, unique=True)
    common_name: Mapped[str | None] = mapped_column(String(160))
    taxonomy_id: Mapped[str | None] = mapped_column(String(32), unique=True)


class ReferenceGenome(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reference_genomes"
    __table_args__ = (UniqueConstraint("organism_id", "assembly_name", "assembly_version"),)

    organism_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organisms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    assembly_name: Mapped[str] = mapped_column(String(160), nullable=False)
    assembly_version: Mapped[str] = mapped_column(String(80), nullable=False)
    fasta_uri: Mapped[str | None] = mapped_column(Text)
    fasta_sha256: Mapped[str | None] = mapped_column(String(64))
    annotation_uri: Mapped[str | None] = mapped_column(Text)
    annotation_format: Mapped[str | None] = mapped_column(String(16))
    annotation_version: Mapped[str | None] = mapped_column(String(80))


class Target(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "targets"
    __table_args__ = (UniqueConstraint("organization_id", "public_id"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    owner_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), index=True)
    owner_project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id"), index=True
    )
    public_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    target_type: Mapped[str] = mapped_column(String(40), nullable=False, default="gene")
    organism_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("organisms.id"), index=True)
    reference_genome_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("reference_genomes.id"), index=True
    )
    gene_identifier: Mapped[str | None] = mapped_column(String(160), index=True)
    transcript_identifier: Mapped[str | None] = mapped_column(String(160), index=True)
    chromosome: Mapped[str | None] = mapped_column(String(80))
    strand: Mapped[str | None] = mapped_column(String(1))
    start: Mapped[int | None] = mapped_column(Integer)
    end: Mapped[int | None] = mapped_column(Integer)
    reference_sequence: Mapped[str | None] = mapped_column(Text)
    aliases: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    external_identifiers: Mapped[dict[str, str]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    description: Mapped[str | None] = mapped_column(Text)
    visibility: Mapped[Visibility] = mapped_column(
        database_enum(Visibility, "target_visibility"), nullable=False, default=Visibility.TEAM
    )
    status: Mapped[RecordStatus] = mapped_column(
        database_enum(RecordStatus, "target_status"), nullable=False, default=RecordStatus.ACTIVE
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)


class ExperimentType(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "experiment_types"

    name: Mapped[str] = mapped_column(String(160), nullable=False, unique=True)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    allowed_roles: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    required_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    recommended_validation_fields: Mapped[dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Oligo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "oligos"
    __table_args__ = (
        UniqueConstraint("organization_id", "public_id", name="uq_oligos_organization_public_id"),
        UniqueConstraint(
            "organization_id",
            "normalized_sequence",
            name="uq_oligos_organization_normalized_sequence",
        ),
        CheckConstraint("sequence_length > 0", name="sequence_length_positive"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    owner_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), index=True)
    owner_project_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("projects.id"), index=True
    )
    public_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    sequence: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_sequence: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    oligo_type: Mapped[str] = mapped_column(String(80), nullable=False, default="DNA")
    description: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    sequence_length: Mapped[int] = mapped_column(Integer, nullable=False)
    gc_percent: Mapped[float | None] = mapped_column(Float)
    melting_temperature_c: Mapped[float | None] = mapped_column(Float)
    molecular_weight_g_mol: Mapped[float | None] = mapped_column(Float)
    reverse_complement: Mapped[str] = mapped_column(Text, nullable=False)
    calculation_provenance: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    visibility: Mapped[Visibility] = mapped_column(
        database_enum(Visibility, "visibility"), nullable=False, default=Visibility.TEAM
    )
    status: Mapped[RecordStatus] = mapped_column(
        database_enum(RecordStatus, "oligo_status"), nullable=False, default=RecordStatus.ACTIVE
    )
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)


class Assay(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "assays"
    __table_args__ = (UniqueConstraint("organization_id", "public_id"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    public_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(240), nullable=False, index=True)
    experiment_type_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("experiment_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    target_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("targets.id"), index=True)
    organism_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("organisms.id"), index=True)
    project_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("projects.id"), index=True)
    owner_team_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("teams.id"), index=True)
    expected_product: Mapped[str | None] = mapped_column(Text)
    expected_amplicon_length: Mapped[int | None] = mapped_column(Integer)
    recommended_annealing_temperature_c: Mapped[float | None] = mapped_column(Float)
    protocol_notes: Mapped[str | None] = mapped_column(Text)
    method_metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    visibility: Mapped[Visibility] = mapped_column(
        database_enum(Visibility, "assay_visibility"), nullable=False, default=Visibility.TEAM
    )
    status: Mapped[RecordStatus] = mapped_column(
        database_enum(RecordStatus, "assay_status"), nullable=False, default=RecordStatus.ACTIVE
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    updated_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    oligos: Mapped[list[AssayOligo]] = relationship(
        back_populates="assay", cascade="all, delete-orphan", lazy="selectin"
    )


class AssayOligo(TimestampMixin, Base):
    __tablename__ = "assay_oligos"

    assay_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("assays.id", ondelete="CASCADE"), primary_key=True
    )
    oligo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("oligos.id", ondelete="RESTRICT"), primary_key=True
    )
    role: Mapped[OligoRole] = mapped_column(
        database_enum(OligoRole, "oligo_role"), primary_key=True
    )
    label: Mapped[str | None] = mapped_column(String(120))
    assay: Mapped[Assay] = relationship(back_populates="oligos")


class PublicIdCounter(Base):
    __tablename__ = "public_id_counters"

    prefix: Mapped[str] = mapped_column(String(8), primary_key=True)
    last_value: Mapped[int] = mapped_column(Integer, nullable=False)


class AuditEvent(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "audit_events"

    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_id: Mapped[uuid.UUID] = mapped_column(nullable=False, index=True)
    before: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    after: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    request_id: Mapped[str | None] = mapped_column(String(80))


@event.listens_for(AuditEvent, "before_insert")
def prepare_audit_event(_: Mapper[AuditEvent], __: Connection, record: AuditEvent) -> None:
    record.request_id = record.request_id or request_id_context.get()
    record.before = safe_audit_facts(record.before)
    record.after = safe_audit_facts(record.after)
