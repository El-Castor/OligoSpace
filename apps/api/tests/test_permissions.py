import uuid

from oligospace_api.domain.permissions import (
    Principal,
    ResourceScope,
    can_create,
    can_edit,
    can_view,
)
from oligospace_api.models.enums import GlobalRole, Visibility

ORG = uuid.uuid4()
USER = uuid.uuid4()
OWNER = uuid.uuid4()
TEAM = uuid.uuid4()
PROJECT = uuid.uuid4()


def principal(role: GlobalRole = GlobalRole.MEMBER) -> Principal:
    return Principal(USER, ORG, role, frozenset({TEAM}), frozenset({PROJECT}))


def test_visibility_boundaries() -> None:
    assert can_view(principal(), ResourceScope(ORG, OWNER, Visibility.ORGANIZATION))
    assert can_view(principal(), ResourceScope(ORG, OWNER, Visibility.TEAM, team_id=TEAM))
    assert can_view(principal(), ResourceScope(ORG, OWNER, Visibility.PROJECT, project_id=PROJECT))
    assert not can_view(principal(), ResourceScope(ORG, OWNER, Visibility.PRIVATE))


def test_cross_organization_is_denied_even_for_admin() -> None:
    resource = ResourceScope(uuid.uuid4(), OWNER, Visibility.ORGANIZATION)
    assert not can_view(principal(GlobalRole.ADMIN), resource)


def test_viewer_cannot_create_or_edit() -> None:
    viewer = principal(GlobalRole.VIEWER)
    resource = ResourceScope(ORG, OWNER, Visibility.TEAM, team_id=TEAM)
    assert not can_create(viewer)
    assert not can_edit(viewer, resource)


def test_team_manager_can_edit_team_resource() -> None:
    resource = ResourceScope(ORG, OWNER, Visibility.TEAM, team_id=TEAM)
    assert can_edit(principal(GlobalRole.TEAM_MANAGER), resource)
