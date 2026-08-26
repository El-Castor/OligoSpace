from __future__ import annotations

import uuid

from pydantic import BaseModel

from oligospace_api.models.enums import GlobalRole


class CurrentUser(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    display_name: str
    role: GlobalRole
    development_identity: bool
