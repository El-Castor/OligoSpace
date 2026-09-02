"""Complete identity and workspace persistence.

Revision ID: 0002_identity_workspaces
Revises: 0001_initial_registry
Create Date: 2026-08-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0002_identity_workspaces"
down_revision: str | None = "0001_initial_registry"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

visibility_values = ("private", "project", "team", "organization")


def upgrade() -> None:
    project_visibility = sa.Enum(*visibility_values, name="project_visibility")
    project_visibility.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "users",
        sa.Column(
            "identity_provider",
            sa.String(80),
            nullable=False,
            server_default="keycloak",
        ),
    )
    op.add_column("users", sa.Column("first_name", sa.String(120)))
    op.add_column("users", sa.Column("last_name", sa.String(120)))
    op.add_column("users", sa.Column("avatar_url", sa.Text()))
    op.add_column("users", sa.Column("last_login_at", sa.DateTime(timezone=True)))
    op.create_index("ix_users_active", "users", ["active"])
    op.create_index("ix_users_global_role", "users", ["global_role"])

    op.add_column(
        "projects",
        sa.Column(
            "visibility",
            project_visibility,
            nullable=False,
            server_default="private",
        ),
    )
    op.add_column("projects", sa.Column("updated_by_id", sa.Uuid()))
    op.execute("UPDATE projects SET updated_by_id = created_by_id WHERE updated_by_id IS NULL")
    op.alter_column("projects", "updated_by_id", nullable=False)
    op.create_foreign_key(
        "fk_projects_updated_by_id_users",
        "projects",
        "users",
        ["updated_by_id"],
        ["id"],
    )
    op.create_index("ix_projects_created_by_id", "projects", ["created_by_id"])
    op.create_index("ix_projects_updated_by_id", "projects", ["updated_by_id"])
    op.create_index("ix_projects_visibility", "projects", ["visibility"])
    op.create_index("ix_projects_status", "projects", ["status"])
    op.create_index("ix_team_memberships_user_id", "team_memberships", ["user_id"])
    op.create_index("ix_project_memberships_user_id", "project_memberships", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_project_memberships_user_id", table_name="project_memberships")
    op.drop_index("ix_team_memberships_user_id", table_name="team_memberships")
    op.drop_index("ix_projects_status", table_name="projects")
    op.drop_index("ix_projects_visibility", table_name="projects")
    op.drop_index("ix_projects_updated_by_id", table_name="projects")
    op.drop_index("ix_projects_created_by_id", table_name="projects")
    op.drop_constraint("fk_projects_updated_by_id_users", "projects", type_="foreignkey")
    op.drop_column("projects", "updated_by_id")
    op.drop_column("projects", "visibility")
    sa.Enum(name="project_visibility").drop(op.get_bind(), checkfirst=True)

    op.drop_index("ix_users_global_role", table_name="users")
    op.drop_index("ix_users_active", table_name="users")
    op.drop_column("users", "last_login_at")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
    op.drop_column("users", "identity_provider")
