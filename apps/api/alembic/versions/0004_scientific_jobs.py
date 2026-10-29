"""Add persistent scientific jobs and Primer3 provenance.

Revision ID: 0004_scientific_jobs
Revises: 0003_experiment_evidence
Create Date: 2026-09-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_scientific_jobs"
down_revision: str | None = "0003_experiment_evidence"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    kind = postgresql.ENUM(
        "oligo_primer3_qc",
        "assay_primer3_pair_compatibility",
        name="scientific_job_kind",
        create_type=False,
    )
    state = postgresql.ENUM(
        "queued",
        "running",
        "retrying",
        "succeeded",
        "failed",
        name="scientific_job_status",
        create_type=False,
    )
    attempt_state = postgresql.ENUM(
        "running", "succeeded", "failed", name="scientific_attempt_status", create_type=False
    )
    visibility = postgresql.ENUM(
        "private",
        "project",
        "team",
        "organization",
        name="scientific_job_visibility",
        create_type=False,
    )
    for enum in (kind, state, attempt_state, visibility):
        enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "scientific_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("requester_id", sa.Uuid(), nullable=False),
        sa.Column("kind", kind, nullable=False),
        sa.Column("state", state, nullable=False),
        sa.Column("visibility", visibility, nullable=False),
        sa.Column("owner_team_id", sa.Uuid()),
        sa.Column("owner_project_id", sa.Uuid()),
        sa.Column("oligo_id", sa.Uuid()),
        sa.Column("assay_id", sa.Uuid()),
        sa.Column("forward_oligo_id", sa.Uuid()),
        sa.Column("reverse_oligo_id", sa.Uuid()),
        sa.Column("assay_version", sa.Integer()),
        sa.Column("input_snapshot", postgresql.JSONB(), nullable=False),
        sa.Column("input_sha256", sa.String(64), nullable=False),
        sa.Column("requested_parameters", postgresql.JSONB(), nullable=False),
        sa.Column("effective_parameters", postgresql.JSONB(), nullable=False),
        sa.Column("parameter_schema_version", sa.String(32), nullable=False),
        sa.Column("execution_fingerprint", sa.String(64), nullable=False),
        sa.Column("idempotency_key", sa.String(128)),
        sa.Column("claim_token", sa.String(36), nullable=False),
        sa.Column("celery_task_id", sa.String(128)),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("next_retry_at", sa.DateTime(timezone=True)),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("last_error_code", sa.String(80)),
        sa.Column("last_error_summary", sa.Text()),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("attempt_count >= 0", name="scientific_job_attempt_count_nonnegative"),
        sa.CheckConstraint(
            "max_attempts BETWEEN 1 AND 10", name="scientific_job_max_attempts_bounded"
        ),
        sa.CheckConstraint(
            "(kind = 'oligo_primer3_qc' AND oligo_id IS NOT NULL "
            "AND assay_id IS NULL AND forward_oligo_id IS NULL "
            "AND reverse_oligo_id IS NULL AND assay_version IS NULL) OR "
            "(kind = 'assay_primer3_pair_compatibility' AND oligo_id IS NULL "
            "AND assay_id IS NOT NULL AND forward_oligo_id IS NOT NULL "
            "AND reverse_oligo_id IS NOT NULL AND assay_version IS NOT NULL)",
            name="scientific_job_subject_shape",
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["requester_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_team_id"], ["teams.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_project_id"], ["projects.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["oligo_id"], ["oligos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assay_id"], ["assays.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["forward_oligo_id"], ["oligos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["reverse_oligo_id"], ["oligos.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id", "public_id", name="uq_scientific_jobs_org_public_id"
        ),
        sa.UniqueConstraint(
            "organization_id",
            "requester_id",
            "idempotency_key",
            name="uq_scientific_jobs_org_requester_idempotency",
        ),
    )
    for column in (
        "organization_id",
        "public_id",
        "requester_id",
        "kind",
        "state",
        "owner_team_id",
        "owner_project_id",
        "oligo_id",
        "assay_id",
    ):
        op.create_index(f"ix_scientific_jobs_{column}", "scientific_jobs", [column])
    op.create_index(
        "ix_scientific_jobs_state_next_retry", "scientific_jobs", ["state", "next_retry_at"]
    )
    op.create_index(
        "ix_scientific_jobs_execution_fingerprint", "scientific_jobs", ["execution_fingerprint"]
    )
    op.create_index(
        "uq_scientific_jobs_active_fingerprint",
        "scientific_jobs",
        ["organization_id", "requester_id", "kind", "execution_fingerprint"],
        unique=True,
        postgresql_where=sa.text("state IN ('queued', 'running', 'retrying')"),
    )

    op.create_table(
        "scientific_job_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("state", attempt_state, nullable=False),
        sa.Column("task_id", sa.String(128)),
        sa.Column("claim_token", sa.String(36), nullable=False),
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.Column("retryable", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("tool_version", sa.String(80)),
        sa.Column("worker_version", sa.String(80)),
        sa.Column("wrapper_contract_version", sa.String(80)),
        sa.Column("build_identity", sa.String(255)),
        sa.Column("exit_status", sa.Integer()),
        sa.Column("error_code", sa.String(80)),
        sa.Column("error_summary", sa.Text()),
        sa.Column(
            "diagnostics", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False
        ),
        sa.ForeignKeyConstraint(["job_id"], ["scientific_jobs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "attempt_number"),
    )
    op.create_index("ix_scientific_job_attempts_job_id", "scientific_job_attempts", ["job_id"])
    op.create_index(
        "ix_scientific_job_attempts_lease_expires_at",
        "scientific_job_attempts",
        ["lease_expires_at"],
    )

    op.create_table(
        "scientific_job_results",
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("result_schema_version", sa.String(32), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "warnings", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False
        ),
        sa.Column("algorithm", sa.String(120), nullable=False),
        sa.Column("tool_version", sa.String(80), nullable=False),
        sa.Column("tool_source_sha256", sa.String(64), nullable=False),
        sa.Column("worker_version", sa.String(80), nullable=False),
        sa.Column("wrapper_contract_version", sa.String(80), nullable=False),
        sa.Column("build_identity", sa.String(255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["scientific_jobs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("job_id"),
    )
    op.execute(
        "INSERT INTO public_id_counters (prefix, last_value) VALUES ('SJOB', 0) "
        "ON CONFLICT (prefix) DO NOTHING"
    )


def downgrade() -> None:
    op.drop_table("scientific_job_results")
    op.drop_table("scientific_job_attempts")
    op.drop_table("scientific_jobs")
    op.execute("DELETE FROM public_id_counters WHERE prefix = 'SJOB'")
    for name in (
        "scientific_job_visibility",
        "scientific_attempt_status",
        "scientific_job_status",
        "scientific_job_kind",
    ):
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
