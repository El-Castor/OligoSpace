"""Add experiment runs, contextual validations, and attachment metadata.

Revision ID: 0003_experiment_evidence
Revises: 0002_identity_workspaces
Create Date: 2026-09-02
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003_experiment_evidence"
down_revision: str | None = "0002_identity_workspaces"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    visibility = postgresql.ENUM(
        "private",
        "project",
        "team",
        "organization",
        name="experiment_run_visibility",
        create_type=False,
    )
    run_status = postgresql.ENUM(
        "active", "deprecated", "archived", name="experiment_run_status", create_type=False
    )
    validation_status = postgresql.ENUM(
        "pending",
        "passed",
        "failed",
        "inconclusive",
        "superseded",
        name="validation_status",
        create_type=False,
    )
    scan_status = postgresql.ENUM(
        "pending",
        "clean",
        "infected",
        "error",
        name="attachment_scan_status",
        create_type=False,
    )
    publication_status = postgresql.ENUM(
        "quarantined",
        "published",
        "rejected",
        "removed",
        name="attachment_publication_status",
        create_type=False,
    )
    for enum in (visibility, run_status, validation_status, scan_status, publication_status):
        enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "experiment_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("assay_id", sa.Uuid(), nullable=False),
        sa.Column("assay_version", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Uuid()),
        sa.Column("owner_team_id", sa.Uuid()),
        sa.Column("operator_id", sa.Uuid(), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("protocol_name", sa.String(240)),
        sa.Column("protocol_version", sa.String(120)),
        sa.Column("conditions", postgresql.JSONB(), nullable=False),
        sa.Column("input_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("visibility", visibility, nullable=False),
        sa.Column("status", run_status, nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("updated_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assay_id"], ["assays.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["owner_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["operator_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "public_id"),
    )
    for column in (
        "organization_id",
        "public_id",
        "assay_id",
        "project_id",
        "owner_team_id",
        "operator_id",
        "performed_at",
    ):
        op.create_index(f"ix_experiment_runs_{column}", "experiment_runs", [column])

    op.create_table(
        "validations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("assay_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_run_id", sa.Uuid()),
        sa.Column("status", validation_status, nullable=False),
        sa.Column("conclusion", sa.Text(), nullable=False),
        sa.Column("measurements", postgresql.JSONB(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("validated_by_id", sa.Uuid(), nullable=False),
        sa.Column("validated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("supersedes_validation_id", sa.Uuid()),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assay_id"], ["assays.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["experiment_run_id"], ["experiment_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["validated_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["supersedes_validation_id"], ["validations.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "public_id"),
        sa.UniqueConstraint("supersedes_validation_id"),
    )
    for column in (
        "organization_id",
        "public_id",
        "assay_id",
        "experiment_run_id",
        "validated_by_id",
        "validated_at",
    ):
        op.create_index(f"ix_validations_{column}", "validations", [column])

    op.create_table(
        "attachments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("experiment_run_id", sa.Uuid()),
        sa.Column("validation_id", sa.Uuid()),
        sa.Column("object_key", sa.String(512), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(160), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("uploaded_by_id", sa.Uuid(), nullable=False),
        sa.Column("scan_status", scan_status, nullable=False),
        sa.Column("publication_status", publication_status, nullable=False),
        sa.Column("replaces_attachment_id", sa.Uuid()),
        sa.Column("removed_at", sa.DateTime(timezone=True)),
        sa.Column("removed_by_id", sa.Uuid()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "num_nonnulls(experiment_run_id, validation_id) = 1",
            name="exactly_one_evidence_parent",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["experiment_run_id"], ["experiment_runs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["validation_id"], ["validations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["uploaded_by_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["replaces_attachment_id"], ["attachments.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["removed_by_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "public_id"),
        sa.UniqueConstraint("object_key"),
    )
    for column in (
        "organization_id",
        "public_id",
        "experiment_run_id",
        "validation_id",
        "sha256",
        "uploaded_by_id",
    ):
        op.create_index(f"ix_attachments_{column}", "attachments", [column])


def downgrade() -> None:
    op.drop_table("attachments")
    op.drop_table("validations")
    op.drop_table("experiment_runs")
    for name in (
        "attachment_publication_status",
        "attachment_scan_status",
        "validation_status",
        "experiment_run_status",
        "experiment_run_visibility",
    ):
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
