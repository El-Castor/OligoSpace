"""Initial collaboration and scientific registry schema.

Revision ID: 0001_initial_registry
Revises: None
Create Date: 2026-08-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001_initial_registry"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

role_values = ("admin", "team_manager", "member", "viewer")
status_values = ("active", "deprecated", "archived")
visibility_values = ("private", "project", "team", "organization")
oligo_role_values = (
    "forward_primer",
    "reverse_primer",
    "probe",
    "internal_oligo",
    "sequencing_primer",
    "adapter",
    "guide",
    "donor",
    "template",
    "other",
)


def timestamps() -> tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def upgrade() -> None:
    op.create_table(
        "organizations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "organisms",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("scientific_name", sa.String(240), nullable=False),
        sa.Column("common_name", sa.String(160)),
        sa.Column("taxonomy_id", sa.String(32)),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("scientific_name"),
        sa.UniqueConstraint("taxonomy_id"),
    )
    op.create_table(
        "experiment_types",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("slug", sa.String(80), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("allowed_roles", postgresql.JSONB(), nullable=False),
        sa.Column("required_metadata", postgresql.JSONB(), nullable=False),
        sa.Column("recommended_validation_fields", postgresql.JSONB(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "public_id_counters",
        sa.Column("prefix", sa.String(8), nullable=False),
        sa.Column("last_value", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("prefix"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("oidc_subject", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("global_role", sa.Enum(*role_values, name="global_role"), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("oidc_subject"),
    )
    op.create_index("ix_users_oidc_subject", "users", ["oidc_subject"])
    op.create_index("ix_users_organization_id", "users", ["organization_id"])
    op.create_table(
        "teams",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("active", sa.Boolean(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "name"),
    )
    op.create_index("ix_teams_organization_id", "teams", ["organization_id"])
    op.create_table(
        "team_memberships",
        sa.Column("team_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Enum(*role_values, name="team_role"), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("team_id", "user_id"),
    )
    op.create_table(
        "projects",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("team_id", sa.Uuid()),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("status", sa.Enum(*status_values, name="record_status"), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["team_id"], ["teams.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "public_id"),
    )
    op.create_index("ix_projects_organization_id", "projects", ["organization_id"])
    op.create_index("ix_projects_public_id", "projects", ["public_id"])
    op.create_index("ix_projects_team_id", "projects", ["team_id"])
    op.create_table(
        "project_memberships",
        sa.Column("project_id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Enum(*role_values, name="project_role"), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("project_id", "user_id"),
    )
    op.create_table(
        "reference_genomes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organism_id", sa.Uuid(), nullable=False),
        sa.Column("assembly_name", sa.String(160), nullable=False),
        sa.Column("assembly_version", sa.String(80), nullable=False),
        sa.Column("fasta_uri", sa.Text()),
        sa.Column("fasta_sha256", sa.String(64)),
        sa.Column("annotation_uri", sa.Text()),
        sa.Column("annotation_format", sa.String(16)),
        sa.Column("annotation_version", sa.String(80)),
        *timestamps(),
        sa.ForeignKeyConstraint(["organism_id"], ["organisms.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organism_id", "assembly_name", "assembly_version"),
    )
    op.create_index("ix_reference_genomes_organism_id", "reference_genomes", ["organism_id"])
    op.create_table(
        "targets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("owner_team_id", sa.Uuid()),
        sa.Column("owner_project_id", sa.Uuid()),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("target_type", sa.String(40), nullable=False),
        sa.Column("organism_id", sa.Uuid()),
        sa.Column("reference_genome_id", sa.Uuid()),
        sa.Column("gene_identifier", sa.String(160)),
        sa.Column("transcript_identifier", sa.String(160)),
        sa.Column("chromosome", sa.String(80)),
        sa.Column("strand", sa.String(1)),
        sa.Column("start", sa.Integer()),
        sa.Column("end", sa.Integer()),
        sa.Column("reference_sequence", sa.Text()),
        sa.Column("aliases", postgresql.JSONB(), nullable=False),
        sa.Column("external_identifiers", postgresql.JSONB(), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column(
            "visibility", sa.Enum(*visibility_values, name="target_visibility"), nullable=False
        ),
        sa.Column("status", sa.Enum(*status_values, name="target_status"), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("updated_by_id", sa.Uuid(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["owner_project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["organism_id"], ["organisms.id"]),
        sa.ForeignKeyConstraint(["reference_genome_id"], ["reference_genomes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "public_id"),
    )
    for column in (
        "organization_id",
        "owner_team_id",
        "owner_project_id",
        "public_id",
        "name",
        "organism_id",
        "reference_genome_id",
        "gene_identifier",
        "transcript_identifier",
    ):
        op.create_index(f"ix_targets_{column}", "targets", [column])
    op.create_table(
        "oligos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("owner_team_id", sa.Uuid()),
        sa.Column("owner_project_id", sa.Uuid()),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("sequence", sa.Text(), nullable=False),
        sa.Column("normalized_sequence", sa.Text(), nullable=False),
        sa.Column("oligo_type", sa.String(80), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("notes", sa.Text()),
        sa.Column("sequence_length", sa.Integer(), nullable=False),
        sa.Column("gc_percent", sa.Float()),
        sa.Column("melting_temperature_c", sa.Float()),
        sa.Column("molecular_weight_g_mol", sa.Float()),
        sa.Column("reverse_complement", sa.Text(), nullable=False),
        sa.Column("calculation_provenance", postgresql.JSONB(), nullable=False),
        sa.Column("visibility", sa.Enum(*visibility_values, name="visibility"), nullable=False),
        sa.Column("status", sa.Enum(*status_values, name="oligo_status"), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("updated_by_id", sa.Uuid(), nullable=False),
        *timestamps(),
        sa.CheckConstraint("sequence_length > 0", name="sequence_length_positive"),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["owner_team_id"], ["teams.id"]),
        sa.ForeignKeyConstraint(["owner_project_id"], ["projects.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "organization_id",
            "normalized_sequence",
            name="uq_oligos_organization_normalized_sequence",
        ),
        sa.UniqueConstraint(
            "organization_id", "public_id", name="uq_oligos_organization_public_id"
        ),
    )
    for column in (
        "organization_id",
        "owner_team_id",
        "owner_project_id",
        "public_id",
        "name",
        "normalized_sequence",
    ):
        op.create_index(f"ix_oligos_{column}", "oligos", [column])
    op.create_table(
        "assays",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("organization_id", sa.Uuid(), nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("experiment_type_id", sa.Uuid(), nullable=False),
        sa.Column("target_id", sa.Uuid()),
        sa.Column("organism_id", sa.Uuid()),
        sa.Column("project_id", sa.Uuid()),
        sa.Column("owner_team_id", sa.Uuid()),
        sa.Column("expected_product", sa.Text()),
        sa.Column("expected_amplicon_length", sa.Integer()),
        sa.Column("recommended_annealing_temperature_c", sa.Float()),
        sa.Column("protocol_notes", sa.Text()),
        sa.Column("method_metadata", postgresql.JSONB(), nullable=False),
        sa.Column(
            "visibility", sa.Enum(*visibility_values, name="assay_visibility"), nullable=False
        ),
        sa.Column("status", sa.Enum(*status_values, name="assay_status"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=False),
        sa.Column("updated_by_id", sa.Uuid(), nullable=False),
        *timestamps(),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"]),
        sa.ForeignKeyConstraint(
            ["experiment_type_id"], ["experiment_types.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(["organization_id"], ["organizations.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["target_id"], ["targets.id"]),
        sa.ForeignKeyConstraint(["organism_id"], ["organisms.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["owner_team_id"], ["teams.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("organization_id", "public_id"),
    )
    for column in (
        "organization_id",
        "public_id",
        "name",
        "experiment_type_id",
        "target_id",
        "organism_id",
        "project_id",
        "owner_team_id",
    ):
        op.create_index(f"ix_assays_{column}", "assays", [column])
    op.create_table(
        "assay_oligos",
        sa.Column("assay_id", sa.Uuid(), nullable=False),
        sa.Column("oligo_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.Enum(*oligo_role_values, name="oligo_role"), nullable=False),
        sa.Column("label", sa.String(120)),
        *timestamps(),
        sa.ForeignKeyConstraint(["assay_id"], ["assays.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["oligo_id"], ["oligos.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("assay_id", "oligo_id", "role"),
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actor_id", sa.Uuid()),
        sa.Column("action", sa.String(80), nullable=False),
        sa.Column("entity_type", sa.String(80), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("before", postgresql.JSONB()),
        sa.Column("after", postgresql.JSONB()),
        sa.Column("request_id", sa.String(80)),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("actor_id", "action", "entity_type", "entity_id"):
        op.create_index(f"ix_audit_events_{column}", "audit_events", [column])


def downgrade() -> None:
    op.drop_table("audit_events")
    op.drop_table("assay_oligos")
    op.drop_table("assays")
    op.drop_table("oligos")
    op.drop_table("targets")
    op.drop_table("reference_genomes")
    op.drop_table("project_memberships")
    op.drop_table("projects")
    op.drop_table("team_memberships")
    op.drop_table("teams")
    op.drop_table("users")
    op.drop_table("public_id_counters")
    op.drop_table("experiment_types")
    op.drop_table("organisms")
    op.drop_table("organizations")
    bind = op.get_bind()
    for enum_name in (
        "oligo_role",
        "assay_status",
        "assay_visibility",
        "oligo_status",
        "visibility",
        "target_status",
        "target_visibility",
        "project_role",
        "record_status",
        "team_role",
        "global_role",
    ):
        sa.Enum(name=enum_name).drop(bind, checkfirst=True)
