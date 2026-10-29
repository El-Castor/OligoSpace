from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from oligospace_api.models.enums import GlobalRole, RecordStatus, Visibility


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserRead(ORMModel):
    id: uuid.UUID
    external_identity_id: str
    identity_provider: str
    email: str
    display_name: str
    first_name: str | None
    last_name: str | None
    avatar_url: str | None
    initials: str
    active: bool
    global_role: GlobalRole
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    last_login_at: datetime | None


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    external_identity_id: str = Field(min_length=2, max_length=255)
    identity_provider: str = Field(default="keycloak", min_length=2, max_length=80)
    email: str = Field(min_length=3, max_length=320)
    display_name: str = Field(min_length=1, max_length=160)
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = None
    global_role: GlobalRole = GlobalRole.MEMBER
    active: bool = True


class UserAdminUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = None
    global_role: GlobalRole | None = None
    active: bool | None = None


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, min_length=1, max_length=160)
    first_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    avatar_url: str | None = None


class MembershipWrite(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: GlobalRole


class MembershipRead(BaseModel):
    user: UserRead
    role: GlobalRole
    created_at: datetime
    updated_at: datetime


class TeamCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=160)
    description: str | None = None


class TeamUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=160)
    description: str | None = None
    active: bool | None = None


class TeamRead(ORMModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None
    active: bool
    member_count: int
    current_user_role: GlobalRole | None
    created_at: datetime
    updated_at: datetime


class LinkedResource(BaseModel):
    public_id: str
    name: str
    status: RecordStatus


class TeamDetail(TeamRead):
    members: list[MembershipRead]
    projects: list[LinkedResource]
    assay_count: int
    oligo_count: int


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=200)
    description: str | None = None
    team_id: uuid.UUID | None = None
    visibility: Visibility = Visibility.PRIVATE


class ProjectUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = None
    team_id: uuid.UUID | None = None
    visibility: Visibility | None = None
    status: RecordStatus | None = None


class ProjectRead(ORMModel):
    id: uuid.UUID
    public_id: str
    organization_id: uuid.UUID
    team_id: uuid.UUID | None
    team_name: str | None
    name: str
    description: str | None
    visibility: Visibility
    status: RecordStatus
    created_by_id: uuid.UUID
    owner_name: str
    current_user_role: GlobalRole | None
    member_count: int
    oligo_count: int
    assay_count: int
    created_at: datetime
    updated_at: datetime


class ProjectDetail(ProjectRead):
    members: list[MembershipRead]
    oligos: list[LinkedResource]
    assays: list[LinkedResource]


class WorkspaceChoices(BaseModel):
    teams: list[TeamRead]
    projects: list[ProjectRead]


class RecentItem(BaseModel):
    entity_type: str
    public_id: str
    name: str
    created_at: datetime


class RecentActivity(BaseModel):
    action: str
    entity_type: str
    entity_id: uuid.UUID
    occurred_at: datetime


class PersonalizedDashboard(BaseModel):
    my_oligos: int
    my_assays: int
    my_projects: int
    team_shared_oligos: int
    visible_targets: int
    visible_projects: int
    recent_items: list[RecentItem]
    recent_activity: list[RecentActivity]
    awaiting_validation: int | None = None
    low_stock: int | None = None
