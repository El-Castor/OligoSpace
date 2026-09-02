from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel

from oligospace_api.models.enums import GlobalRole


class CurrentTeam(BaseModel):
    id: uuid.UUID
    name: str
    role: GlobalRole


class CurrentUser(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    display_name: str
    first_name: str | None
    last_name: str | None
    avatar_url: str | None
    initials: str
    identity_provider: str
    external_identity_id: str
    active: bool
    role: GlobalRole
    development_identity: bool
    organization_name: str
    teams: list[CurrentTeam]
    created_at: datetime
    last_login_at: datetime | None
