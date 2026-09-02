from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.domain.permissions import (
    Principal,
    can_create,
    can_manage_project,
    can_manage_team,
)
from oligospace_api.models.enums import GlobalRole, ValidationStatus, Visibility
from oligospace_api.models.laboratory import ExperimentRun, Validation
from oligospace_api.models.registry import (
    Assay,
    AuditEvent,
    Oligo,
    Project,
    ProjectMembership,
    Target,
    Team,
    TeamMembership,
    User,
)
from oligospace_api.repositories.laboratory import visible_run_query
from oligospace_api.repositories.registry import visible_query
from oligospace_api.repositories.workspace import (
    get_visible_project,
    get_visible_team,
    list_visible_projects,
    list_visible_teams,
    visible_projects_query,
)
from oligospace_api.schemas.workspace import (
    LinkedResource,
    MembershipRead,
    PersonalizedDashboard,
    ProfileUpdate,
    ProjectCreate,
    ProjectDetail,
    ProjectRead,
    ProjectUpdate,
    RecentActivity,
    RecentItem,
    TeamCreate,
    TeamDetail,
    TeamRead,
    TeamUpdate,
    UserAdminUpdate,
    UserCreate,
    UserRead,
)
from oligospace_api.services.public_ids import allocate_public_id


def _forbidden(message: str = "This action is not permitted.") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "forbidden", "message": message},
    )


def _not_found(entity: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "not_found", "message": f"{entity} was not found."},
    )


def _json_value(value: Any) -> Any:
    if isinstance(value, uuid.UUID):
        return str(value)
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {key: _json_value(item) for key, item in value.items()}
    return value


def _audit(
    actor_id: uuid.UUID,
    action: str,
    entity_type: str,
    entity_id: uuid.UUID,
    *,
    before: dict[str, Any] | None = None,
    after: dict[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent(
        occurred_at=datetime.now(UTC),
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before=_json_value(before),
        after=_json_value(after),
    )


def _initials(user: User) -> str:
    parts = [part for part in (user.first_name, user.last_name) if part]
    if not parts:
        parts = user.display_name.split()
    return "".join(part[0].upper() for part in parts[:2]) or "?"


def user_read(user: User) -> UserRead:
    return UserRead(
        id=user.id,
        external_identity_id=user.oidc_subject,
        identity_provider=user.identity_provider,
        email=user.email,
        display_name=user.display_name,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar_url=user.avatar_url,
        initials=_initials(user),
        active=user.active,
        global_role=user.global_role,
        organization_id=user.organization_id,
        created_at=user.created_at,
        updated_at=user.updated_at,
        last_login_at=user.last_login_at,
    )


def _require_admin(principal: Principal) -> None:
    if principal.role is not GlobalRole.ADMIN:
        raise _forbidden("Administrator role required.")


async def create_user(session: AsyncSession, principal: Principal, payload: UserCreate) -> User:
    _require_admin(principal)
    existing = await session.scalar(
        select(User).where(
            or_(
                User.oidc_subject == payload.external_identity_id,
                func.lower(User.email) == payload.email.strip().lower(),
            )
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "user_identity_conflict", "message": "User already exists."},
        )
    user = User(
        oidc_subject=payload.external_identity_id.strip(),
        identity_provider=payload.identity_provider.strip(),
        email=payload.email.strip().lower(),
        display_name=payload.display_name.strip(),
        first_name=payload.first_name,
        last_name=payload.last_name,
        avatar_url=payload.avatar_url,
        active=payload.active,
        global_role=payload.global_role,
        organization_id=principal.organization_id,
    )
    session.add(user)
    await session.flush()
    session.add(
        _audit(
            principal.user_id,
            "create",
            "user",
            user.id,
            after={
                "email": user.email,
                "display_name": user.display_name,
                "global_role": user.global_role,
                "active": user.active,
                "identity_provider": user.identity_provider,
            },
        )
    )
    await session.commit()
    await session.refresh(user)
    return user


async def update_user(
    session: AsyncSession,
    principal: Principal,
    user_id: uuid.UUID,
    payload: UserAdminUpdate,
) -> User:
    _require_admin(principal)
    user = await session.scalar(
        select(User).where(User.id == user_id, User.organization_id == principal.organization_id)
    )
    if user is None:
        raise _not_found("User")
    data = payload.model_dump(exclude_unset=True)
    if user.id == principal.user_id and (
        data.get("active") is False
        or (
            "global_role" in data
            and data["global_role"] is not None
            and data["global_role"] is not GlobalRole.ADMIN
        )
    ):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "cannot_remove_own_admin_access",
                "message": "Use another administrator to change your own access.",
            },
        )
    before = {
        "display_name": user.display_name,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "avatar_url": user.avatar_url,
        "global_role": user.global_role,
        "active": user.active,
    }
    for field, value in data.items():
        setattr(user, field, value)
    await session.flush()
    session.add(
        _audit(
            principal.user_id,
            "update",
            "user",
            user.id,
            before=before,
            after={
                "display_name": user.display_name,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "avatar_url": user.avatar_url,
                "global_role": user.global_role,
                "active": user.active,
            },
        )
    )
    await session.commit()
    await session.refresh(user)
    return user


async def update_profile(
    session: AsyncSession, principal: Principal, payload: ProfileUpdate
) -> User:
    user = await session.scalar(select(User).where(User.id == principal.user_id))
    if user is None:
        raise _not_found("User")
    data = payload.model_dump(exclude_unset=True)
    before = {field: getattr(user, field) for field in data}
    for field, value in data.items():
        setattr(user, field, value)
    if data:
        await session.flush()
        session.add(
            _audit(
                principal.user_id,
                "update_profile",
                "user",
                user.id,
                before=before,
                after={field: getattr(user, field) for field in data},
            )
        )
        await session.commit()
        await session.refresh(user)
    return user


async def _team_read(session: AsyncSession, principal: Principal, team: Team) -> TeamRead:
    member_count = int(
        await session.scalar(
            select(func.count())
            .select_from(TeamMembership)
            .where(TeamMembership.team_id == team.id)
        )
        or 0
    )
    return TeamRead(
        id=team.id,
        organization_id=team.organization_id,
        name=team.name,
        description=team.description,
        active=team.active,
        member_count=member_count,
        current_user_role=(
            GlobalRole.ADMIN if principal.role is GlobalRole.ADMIN else principal.team_role(team.id)
        ),
        created_at=team.created_at,
        updated_at=team.updated_at,
    )


async def team_reads(
    session: AsyncSession, principal: Principal, teams: list[Team]
) -> list[TeamRead]:
    return [await _team_read(session, principal, team) for team in teams]


async def create_team(session: AsyncSession, principal: Principal, payload: TeamCreate) -> Team:
    _require_admin(principal)
    existing = await session.scalar(
        select(Team).where(
            Team.organization_id == principal.organization_id,
            func.lower(Team.name) == payload.name.strip().lower(),
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail={"code": "team_name_conflict"})
    team = Team(
        organization_id=principal.organization_id,
        name=payload.name.strip(),
        description=payload.description,
        active=True,
    )
    session.add(team)
    await session.flush()
    membership = TeamMembership(team_id=team.id, user_id=principal.user_id, role=GlobalRole.ADMIN)
    session.add(membership)
    session.add(
        _audit(
            principal.user_id,
            "create",
            "team",
            team.id,
            after={"name": team.name, "active": team.active},
        )
    )
    await session.commit()
    await session.refresh(team)
    return team


async def update_team(
    session: AsyncSession,
    principal: Principal,
    team_id: uuid.UUID,
    payload: TeamUpdate,
) -> Team:
    team = await get_visible_team(session, principal, team_id)
    if team is None:
        raise _not_found("Team")
    if not can_manage_team(principal, team.id):
        raise _forbidden()
    data = payload.model_dump(exclude_unset=True)
    before = {field: getattr(team, field) for field in data}
    for field, value in data.items():
        setattr(team, field, value)
    if data:
        await session.flush()
        session.add(
            _audit(
                principal.user_id,
                "update",
                "team",
                team.id,
                before=before,
                after={field: getattr(team, field) for field in data},
            )
        )
        await session.commit()
        await session.refresh(team)
    return team


async def set_team_membership(
    session: AsyncSession,
    principal: Principal,
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    role: GlobalRole,
) -> TeamMembership:
    team = await get_visible_team(session, principal, team_id)
    if team is None:
        raise _not_found("Team")
    if not can_manage_team(principal, team.id):
        raise _forbidden()
    user = await session.scalar(
        select(User).where(
            User.id == user_id,
            User.organization_id == principal.organization_id,
            User.active.is_(True),
        )
    )
    if user is None:
        raise _not_found("Active user")
    membership = await session.get(TeamMembership, (team_id, user_id))
    before = {"role": membership.role} if membership is not None else None
    if membership is None:
        membership = TeamMembership(team_id=team_id, user_id=user_id, role=role)
        session.add(membership)
        action = "add_member"
    else:
        membership.role = role
        action = "change_member_role"
    await session.flush()
    session.add(
        _audit(
            principal.user_id,
            action,
            "team_membership",
            team_id,
            before=before,
            after={"user_id": user_id, "role": role},
        )
    )
    await session.commit()
    await session.refresh(membership)
    return membership


async def remove_team_membership(
    session: AsyncSession,
    principal: Principal,
    team_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    team = await get_visible_team(session, principal, team_id)
    if team is None:
        raise _not_found("Team")
    if not can_manage_team(principal, team.id):
        raise _forbidden()
    membership = await session.get(TeamMembership, (team_id, user_id))
    if membership is None:
        raise _not_found("Team membership")
    if user_id == principal.user_id and principal.role is not GlobalRole.ADMIN:
        raise HTTPException(status_code=422, detail={"code": "cannot_remove_self"})
    before = {"user_id": user_id, "role": membership.role}
    await session.delete(membership)
    session.add(
        _audit(
            principal.user_id,
            "remove_member",
            "team_membership",
            team_id,
            before=before,
        )
    )
    await session.commit()


async def team_detail(
    session: AsyncSession, principal: Principal, team_id: uuid.UUID
) -> TeamDetail:
    team = await get_visible_team(session, principal, team_id)
    if team is None:
        raise _not_found("Team")
    base = await _team_read(session, principal, team)
    membership_rows = (
        await session.execute(
            select(TeamMembership, User)
            .join(User, User.id == TeamMembership.user_id)
            .where(TeamMembership.team_id == team.id)
            .order_by(User.display_name)
        )
    ).all()
    projects = list(
        (
            await session.scalars(
                visible_projects_query(principal)
                .where(Project.team_id == team.id)
                .order_by(Project.name)
            )
        ).all()
    )
    assay_count = int(
        await session.scalar(
            select(func.count()).select_from(
                visible_query(Assay, principal).where(Assay.owner_team_id == team.id).subquery()
            )
        )
        or 0
    )
    oligo_count = int(
        await session.scalar(
            select(func.count()).select_from(
                visible_query(Oligo, principal).where(Oligo.owner_team_id == team.id).subquery()
            )
        )
        or 0
    )
    return TeamDetail(
        **base.model_dump(),
        members=[
            MembershipRead(
                user=user_read(user),
                role=membership.role,
                created_at=membership.created_at,
                updated_at=membership.updated_at,
            )
            for membership, user in membership_rows
        ],
        projects=[
            LinkedResource(public_id=item.public_id, name=item.name, status=item.status)
            for item in projects
        ],
        assay_count=assay_count,
        oligo_count=oligo_count,
    )


async def _project_read(
    session: AsyncSession, principal: Principal, project: Project
) -> ProjectRead:
    team_name = (
        await session.scalar(select(Team.name).where(Team.id == project.team_id))
        if project.team_id
        else None
    )
    owner_name = await session.scalar(
        select(User.display_name).where(User.id == project.created_by_id)
    )
    member_count = int(
        await session.scalar(
            select(func.count())
            .select_from(ProjectMembership)
            .where(ProjectMembership.project_id == project.id)
        )
        or 0
    )
    oligo_count = int(
        await session.scalar(
            select(func.count()).select_from(
                visible_query(Oligo, principal)
                .where(Oligo.owner_project_id == project.id)
                .subquery()
            )
        )
        or 0
    )
    assay_count = int(
        await session.scalar(
            select(func.count()).select_from(
                visible_query(Assay, principal).where(Assay.project_id == project.id).subquery()
            )
        )
        or 0
    )
    return ProjectRead(
        id=project.id,
        public_id=project.public_id,
        organization_id=project.organization_id,
        team_id=project.team_id,
        team_name=team_name,
        name=project.name,
        description=project.description,
        visibility=project.visibility,
        status=project.status,
        created_by_id=project.created_by_id,
        owner_name=owner_name or "Unknown user",
        current_user_role=(
            GlobalRole.ADMIN
            if principal.role is GlobalRole.ADMIN or principal.user_id == project.created_by_id
            else principal.project_role(project.id)
        ),
        member_count=member_count,
        oligo_count=oligo_count,
        assay_count=assay_count,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def project_reads(
    session: AsyncSession, principal: Principal, projects: list[Project]
) -> list[ProjectRead]:
    return [await _project_read(session, principal, project) for project in projects]


async def _validate_project_team(
    session: AsyncSession,
    principal: Principal,
    team_id: uuid.UUID | None,
    visibility: Visibility,
) -> Team | None:
    if visibility is Visibility.TEAM and team_id is None:
        raise HTTPException(
            status_code=422,
            detail={"code": "team_visibility_requires_team"},
        )
    if team_id is None:
        return None
    team = await get_visible_team(session, principal, team_id)
    if team is None or not team.active:
        raise HTTPException(status_code=422, detail={"code": "unknown_or_inaccessible_team"})
    return team


async def create_project(
    session: AsyncSession, principal: Principal, payload: ProjectCreate
) -> Project:
    if not can_create(principal):
        raise _forbidden("This role cannot create projects.")
    await _validate_project_team(session, principal, payload.team_id, payload.visibility)
    project = Project(
        organization_id=principal.organization_id,
        team_id=payload.team_id,
        public_id=await allocate_public_id(session, "PRJ"),
        name=payload.name.strip(),
        description=payload.description,
        visibility=payload.visibility,
        created_by_id=principal.user_id,
        updated_by_id=principal.user_id,
    )
    session.add(project)
    await session.flush()
    session.add(
        ProjectMembership(
            project_id=project.id,
            user_id=principal.user_id,
            role=GlobalRole.ADMIN,
        )
    )
    session.add(
        _audit(
            principal.user_id,
            "create",
            "project",
            project.id,
            after={
                "public_id": project.public_id,
                "name": project.name,
                "team_id": project.team_id,
                "visibility": project.visibility,
            },
        )
    )
    await session.commit()
    await session.refresh(project)
    return project


async def update_project(
    session: AsyncSession,
    principal: Principal,
    public_id: str,
    payload: ProjectUpdate,
) -> Project:
    project = await get_visible_project(session, principal, public_id)
    if project is None:
        raise _not_found("Project")
    if not (
        principal.user_id == project.created_by_id or can_manage_project(principal, project.id)
    ):
        raise _forbidden()
    data = payload.model_dump(exclude_unset=True)
    effective_team_id = data.get("team_id", project.team_id)
    effective_visibility = data.get("visibility", project.visibility)
    await _validate_project_team(session, principal, effective_team_id, effective_visibility)
    before = {
        "name": project.name,
        "description": project.description,
        "team_id": project.team_id,
        "visibility": project.visibility,
        "status": project.status,
    }
    for field, value in data.items():
        setattr(project, field, value)
    project.updated_by_id = principal.user_id
    if data:
        await session.flush()
        session.add(
            _audit(
                principal.user_id,
                "update",
                "project",
                project.id,
                before=before,
                after={
                    "name": project.name,
                    "description": project.description,
                    "team_id": project.team_id,
                    "visibility": project.visibility,
                    "status": project.status,
                },
            )
        )
        await session.commit()
        await session.refresh(project)
    return project


async def set_project_membership(
    session: AsyncSession,
    principal: Principal,
    public_id: str,
    user_id: uuid.UUID,
    role: GlobalRole,
) -> ProjectMembership:
    project = await get_visible_project(session, principal, public_id)
    if project is None:
        raise _not_found("Project")
    if not (
        principal.user_id == project.created_by_id or can_manage_project(principal, project.id)
    ):
        raise _forbidden()
    user = await session.scalar(
        select(User).where(
            User.id == user_id,
            User.organization_id == principal.organization_id,
            User.active.is_(True),
        )
    )
    if user is None:
        raise _not_found("Active user")
    membership = await session.get(ProjectMembership, (project.id, user_id))
    before = {"role": membership.role} if membership else None
    if membership is None:
        membership = ProjectMembership(project_id=project.id, user_id=user_id, role=role)
        session.add(membership)
        action = "add_member"
    else:
        membership.role = role
        action = "change_member_role"
    await session.flush()
    session.add(
        _audit(
            principal.user_id,
            action,
            "project_membership",
            project.id,
            before=before,
            after={"user_id": user_id, "role": role},
        )
    )
    await session.commit()
    await session.refresh(membership)
    return membership


async def remove_project_membership(
    session: AsyncSession,
    principal: Principal,
    public_id: str,
    user_id: uuid.UUID,
) -> None:
    project = await get_visible_project(session, principal, public_id)
    if project is None:
        raise _not_found("Project")
    if not (
        principal.user_id == project.created_by_id or can_manage_project(principal, project.id)
    ):
        raise _forbidden()
    if user_id == project.created_by_id:
        raise HTTPException(status_code=422, detail={"code": "cannot_remove_project_owner"})
    membership = await session.get(ProjectMembership, (project.id, user_id))
    if membership is None:
        raise _not_found("Project membership")
    before = {"user_id": user_id, "role": membership.role}
    await session.delete(membership)
    session.add(
        _audit(
            principal.user_id,
            "remove_member",
            "project_membership",
            project.id,
            before=before,
        )
    )
    await session.commit()


async def project_detail(
    session: AsyncSession, principal: Principal, public_id: str
) -> ProjectDetail:
    project = await get_visible_project(session, principal, public_id)
    if project is None:
        raise _not_found("Project")
    base = await _project_read(session, principal, project)
    membership_rows = (
        await session.execute(
            select(ProjectMembership, User)
            .join(User, User.id == ProjectMembership.user_id)
            .where(ProjectMembership.project_id == project.id)
            .order_by(User.display_name)
        )
    ).all()
    oligos = list(
        (
            await session.scalars(
                visible_query(Oligo, principal)
                .where(Oligo.owner_project_id == project.id)
                .order_by(Oligo.name)
            )
        ).all()
    )
    assays = list(
        (
            await session.scalars(
                visible_query(Assay, principal)
                .where(Assay.project_id == project.id)
                .order_by(Assay.name)
            )
        ).all()
    )
    return ProjectDetail(
        **base.model_dump(),
        members=[
            MembershipRead(
                user=user_read(user),
                role=membership.role,
                created_at=membership.created_at,
                updated_at=membership.updated_at,
            )
            for membership, user in membership_rows
        ],
        oligos=[
            LinkedResource(public_id=item.public_id, name=item.name, status=item.status)
            for item in oligos
        ],
        assays=[
            LinkedResource(public_id=item.public_id, name=item.name, status=item.status)
            for item in assays
        ],
    )


async def validate_resource_scope(
    session: AsyncSession,
    principal: Principal,
    *,
    visibility: Visibility,
    team_id: uuid.UUID | None,
    project_id: uuid.UUID | None,
) -> None:
    team: Team | None = None
    project: Project | None = None
    if team_id is not None:
        team = await get_visible_team(session, principal, team_id)
        if team is None or not team.active:
            raise HTTPException(status_code=422, detail={"code": "unknown_or_inaccessible_team"})
    if project_id is not None:
        project = await session.scalar(
            visible_projects_query(principal).where(Project.id == project_id)
        )
        if project is None or project.status.value == "archived":
            raise HTTPException(status_code=422, detail={"code": "unknown_or_inaccessible_project"})
    if visibility is Visibility.TEAM and team is None:
        raise HTTPException(status_code=422, detail={"code": "team_visibility_requires_team"})
    if visibility is Visibility.PROJECT and project is None:
        raise HTTPException(status_code=422, detail={"code": "project_visibility_requires_project"})
    if team is not None and project is not None and project.team_id not in (None, team.id):
        raise HTTPException(status_code=422, detail={"code": "project_team_mismatch"})


async def personalized_dashboard(
    session: AsyncSession, principal: Principal
) -> PersonalizedDashboard:
    async def count(statement: Any) -> int:
        return int(
            await session.scalar(select(func.count()).select_from(statement.subquery())) or 0
        )

    my_oligos = await count(
        visible_query(Oligo, principal).where(Oligo.created_by_id == principal.user_id)
    )
    my_assays = await count(
        visible_query(Assay, principal).where(Assay.created_by_id == principal.user_id)
    )
    my_projects = await count(
        visible_projects_query(principal).where(
            or_(
                Project.created_by_id == principal.user_id,
                Project.id.in_(principal.project_ids),
            )
        )
    )
    team_shared_oligos = await count(
        visible_query(Oligo, principal).where(
            Oligo.visibility == Visibility.TEAM,
            Oligo.owner_team_id.in_(principal.team_ids),
            Oligo.created_by_id != principal.user_id,
        )
    )
    visible_targets = await count(visible_query(Target, principal))
    visible_projects = await count(visible_projects_query(principal))
    has_conclusion = exists(
        select(Validation.id).where(
            Validation.experiment_run_id == ExperimentRun.id,
            Validation.status.in_(
                (
                    ValidationStatus.PASSED,
                    ValidationStatus.FAILED,
                    ValidationStatus.INCONCLUSIVE,
                )
            ),
        )
    )
    awaiting_validation = await count(visible_run_query(principal).where(~has_conclusion))

    recent_items: list[RecentItem] = []
    for entity_type, model, statement in (
        ("oligo", Oligo, visible_query(Oligo, principal)),
        ("assay", Assay, visible_query(Assay, principal)),
        ("project", Project, visible_projects_query(principal)),
    ):
        items = list(
            (await session.scalars(statement.order_by(model.created_at.desc()).limit(5))).all()
        )
        recent_items.extend(
            RecentItem(
                entity_type=entity_type,
                public_id=item.public_id,
                name=item.name,
                created_at=item.created_at,
            )
            for item in items
        )
    recent_items.sort(key=lambda item: item.created_at, reverse=True)

    activities = list(
        (
            await session.scalars(
                select(AuditEvent)
                .where(AuditEvent.actor_id == principal.user_id)
                .order_by(AuditEvent.occurred_at.desc())
                .limit(10)
            )
        ).all()
    )
    return PersonalizedDashboard(
        my_oligos=my_oligos,
        my_assays=my_assays,
        my_projects=my_projects,
        team_shared_oligos=team_shared_oligos,
        visible_targets=visible_targets,
        visible_projects=visible_projects,
        recent_items=recent_items[:10],
        recent_activity=[
            RecentActivity(
                action=item.action,
                entity_type=item.entity_type,
                entity_id=item.entity_id,
                occurred_at=item.occurred_at,
            )
            for item in activities
        ],
        awaiting_validation=awaiting_validation,
    )


async def workspace_choices(
    session: AsyncSession, principal: Principal
) -> tuple[list[TeamRead], list[ProjectRead]]:
    teams = await list_visible_teams(session, principal)
    projects = await list_visible_projects(session, principal)
    return (
        await team_reads(session, principal, teams),
        await project_reads(session, principal, projects),
    )
