from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from oligospace_api.models.enums import GlobalRole, Visibility


@dataclass(frozen=True)
class Principal:
    user_id: uuid.UUID
    organization_id: uuid.UUID
    role: GlobalRole
    team_ids: frozenset[uuid.UUID] = field(default_factory=frozenset)
    project_ids: frozenset[uuid.UUID] = field(default_factory=frozenset)
    team_roles: Mapping[uuid.UUID, GlobalRole] = field(default_factory=lambda: MappingProxyType({}))
    project_roles: Mapping[uuid.UUID, GlobalRole] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def team_role(self, team_id: uuid.UUID | None) -> GlobalRole | None:
        return self.team_roles.get(team_id) if team_id is not None else None

    def project_role(self, project_id: uuid.UUID | None) -> GlobalRole | None:
        return self.project_roles.get(project_id) if project_id is not None else None


@dataclass(frozen=True)
class ResourceScope:
    organization_id: uuid.UUID
    created_by_id: uuid.UUID
    visibility: Visibility
    team_id: uuid.UUID | None = None
    project_id: uuid.UUID | None = None


def can_view(principal: Principal, resource: ResourceScope) -> bool:
    if principal.organization_id != resource.organization_id:
        return False
    if principal.role is GlobalRole.ADMIN or principal.user_id == resource.created_by_id:
        return True
    if resource.visibility is Visibility.ORGANIZATION:
        return True
    if resource.visibility is Visibility.TEAM:
        return resource.team_id is not None and resource.team_id in principal.team_ids
    if resource.visibility is Visibility.PROJECT:
        return resource.project_id is not None and resource.project_id in principal.project_ids
    return False


def can_create(principal: Principal) -> bool:
    return principal.role in {GlobalRole.ADMIN, GlobalRole.TEAM_MANAGER, GlobalRole.MEMBER}


def can_manage_catalog(principal: Principal) -> bool:
    return principal.role is GlobalRole.ADMIN


def can_manage_team(principal: Principal, team_id: uuid.UUID) -> bool:
    if principal.role is GlobalRole.ADMIN:
        return True
    return principal.team_role(team_id) in {GlobalRole.ADMIN, GlobalRole.TEAM_MANAGER}


def can_manage_project(principal: Principal, project_id: uuid.UUID) -> bool:
    if principal.role is GlobalRole.ADMIN:
        return True
    return principal.project_role(project_id) in {
        GlobalRole.ADMIN,
        GlobalRole.TEAM_MANAGER,
    }


def can_edit(principal: Principal, resource: ResourceScope) -> bool:
    if not can_view(principal, resource):
        return False
    return (
        principal.role is GlobalRole.ADMIN
        or principal.user_id == resource.created_by_id
        or principal.team_role(resource.team_id) in {GlobalRole.ADMIN, GlobalRole.TEAM_MANAGER}
        or principal.project_role(resource.project_id)
        in {GlobalRole.ADMIN, GlobalRole.TEAM_MANAGER}
    )
