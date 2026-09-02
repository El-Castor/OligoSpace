from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.db.session import get_session
from oligospace_api.models.enums import GlobalRole
from oligospace_api.repositories.workspace import (
    list_organization_users,
    list_visible_projects,
    list_visible_teams,
)
from oligospace_api.schemas.workspace import (
    MembershipWrite,
    PersonalizedDashboard,
    ProfileUpdate,
    ProjectCreate,
    ProjectDetail,
    ProjectRead,
    ProjectUpdate,
    TeamCreate,
    TeamDetail,
    TeamRead,
    TeamUpdate,
    UserAdminUpdate,
    UserCreate,
    UserRead,
    WorkspaceChoices,
)
from oligospace_api.security.auth import AuthContext, get_auth_context
from oligospace_api.services.workspace import (
    create_project,
    create_team,
    create_user,
    personalized_dashboard,
    project_detail,
    project_reads,
    remove_project_membership,
    remove_team_membership,
    set_project_membership,
    set_team_membership,
    team_detail,
    team_reads,
    update_profile,
    update_project,
    update_team,
    update_user,
    user_read,
    workspace_choices,
)

router = APIRouter(prefix="/workspace", tags=["workspace"])


def _admin(context: AuthContext) -> None:
    if context.principal.role is not GlobalRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "Administrator role required."},
        )


@router.patch("/profile", response_model=UserRead)
async def edit_profile(
    payload: ProfileUpdate,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    return user_read(await update_profile(session, context.principal, payload))


@router.get("/dashboard", response_model=PersonalizedDashboard)
async def dashboard(
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> PersonalizedDashboard:
    return await personalized_dashboard(session, context.principal)


@router.get("/choices", response_model=WorkspaceChoices)
async def choices(
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> WorkspaceChoices:
    teams, projects = await workspace_choices(session, context.principal)
    return WorkspaceChoices(teams=teams, projects=projects)


@router.get("/teams", response_model=list[TeamRead])
async def teams(
    q: str | None = Query(default=None, max_length=200),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[TeamRead]:
    items = await list_visible_teams(session, context.principal, q)
    return await team_reads(session, context.principal, items)


@router.post("/teams", response_model=TeamRead, status_code=201)
async def add_team(
    payload: TeamCreate,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> TeamRead:
    item = await create_team(session, context.principal, payload)
    return (await team_reads(session, context.principal, [item]))[0]


@router.get("/teams/{team_id}", response_model=TeamDetail)
async def get_team(
    team_id: uuid.UUID,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> TeamDetail:
    return await team_detail(session, context.principal, team_id)


@router.patch("/teams/{team_id}", response_model=TeamRead)
async def edit_team(
    payload: TeamUpdate,
    team_id: uuid.UUID,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> TeamRead:
    item = await update_team(session, context.principal, team_id, payload)
    return (await team_reads(session, context.principal, [item]))[0]


@router.put("/teams/{team_id}/members/{user_id}", response_model=TeamDetail)
async def put_team_member(
    payload: MembershipWrite,
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> TeamDetail:
    await set_team_membership(session, context.principal, team_id, user_id, payload.role)
    return await team_detail(session, context.principal, team_id)


@router.delete("/teams/{team_id}/members/{user_id}", status_code=204)
async def delete_team_member(
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await remove_team_membership(session, context.principal, team_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/projects", response_model=list[ProjectRead])
async def projects(
    q: str | None = Query(default=None, max_length=200),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[ProjectRead]:
    items = await list_visible_projects(session, context.principal, q)
    return await project_reads(session, context.principal, items)


@router.post("/projects", response_model=ProjectRead, status_code=201)
async def add_project(
    payload: ProjectCreate,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ProjectRead:
    item = await create_project(session, context.principal, payload)
    return (await project_reads(session, context.principal, [item]))[0]


@router.get("/projects/{public_id}", response_model=ProjectDetail)
async def get_project(
    public_id: str,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ProjectDetail:
    return await project_detail(session, context.principal, public_id)


@router.patch("/projects/{public_id}", response_model=ProjectRead)
async def edit_project(
    payload: ProjectUpdate,
    public_id: str,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ProjectRead:
    item = await update_project(session, context.principal, public_id, payload)
    return (await project_reads(session, context.principal, [item]))[0]


@router.put("/projects/{public_id}/members/{user_id}", response_model=ProjectDetail)
async def put_project_member(
    payload: MembershipWrite,
    public_id: str,
    user_id: uuid.UUID,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> ProjectDetail:
    await set_project_membership(session, context.principal, public_id, user_id, payload.role)
    return await project_detail(session, context.principal, public_id)


@router.delete("/projects/{public_id}/members/{user_id}", status_code=204)
async def delete_project_member(
    public_id: str,
    user_id: uuid.UUID,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> Response:
    await remove_project_membership(session, context.principal, public_id, user_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/admin/users", response_model=list[UserRead])
async def users(
    q: str | None = Query(default=None, max_length=200),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[UserRead]:
    _admin(context)
    items = await list_organization_users(session, context.principal, q)
    return [user_read(item) for item in items]


@router.get("/users", response_model=list[UserRead])
async def membership_candidates(
    q: str | None = Query(default=None, max_length=200),
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> list[UserRead]:
    manager_roles = {GlobalRole.ADMIN, GlobalRole.TEAM_MANAGER}
    can_manage_memberships = (
        context.principal.role is GlobalRole.ADMIN
        or any(role in manager_roles for role in context.principal.team_roles.values())
        or any(role in manager_roles for role in context.principal.project_roles.values())
    )
    if not can_manage_memberships:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "forbidden", "message": "Manager role required."},
        )
    return [
        user_read(item) for item in await list_organization_users(session, context.principal, q)
    ]


@router.post("/admin/users", response_model=UserRead, status_code=201)
async def add_user(
    payload: UserCreate,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    return user_read(await create_user(session, context.principal, payload))


@router.patch("/admin/users/{user_id}", response_model=UserRead)
async def edit_user(
    payload: UserAdminUpdate,
    user_id: uuid.UUID,
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    return user_read(await update_user(session, context.principal, user_id, payload))
