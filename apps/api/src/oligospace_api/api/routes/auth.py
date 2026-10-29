from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.db.session import get_session
from oligospace_api.models.registry import Organization, Team
from oligospace_api.schemas.auth import CurrentTeam, CurrentUser
from oligospace_api.security.auth import AuthContext, get_auth_context

router = APIRouter(prefix="/me", tags=["identity"])


def _initials(display_name: str, first_name: str | None, last_name: str | None) -> str:
    parts = [part for part in (first_name, last_name) if part]
    if not parts:
        parts = display_name.split()
    return "".join(part[0].upper() for part in parts[:2]) or "?"


@router.get("", response_model=CurrentUser)
async def current_user(
    context: AuthContext = Depends(get_auth_context),
    session: AsyncSession = Depends(get_session),
) -> CurrentUser:
    if context.user is None:  # Defensive: all configured auth modes project a user.
        raise RuntimeError("Authenticated context has no projected user")
    user = context.user
    organization_name = await session.scalar(
        select(Organization.name).where(Organization.id == user.organization_id)
    )
    teams = list(
        (
            await session.scalars(
                select(Team).where(Team.id.in_(context.principal.team_ids)).order_by(Team.name)
            )
        ).all()
    )
    return CurrentUser(
        id=context.principal.user_id,
        organization_id=context.principal.organization_id,
        email=context.email,
        display_name=context.display_name,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar_url=user.avatar_url,
        initials=_initials(user.display_name, user.first_name, user.last_name),
        identity_provider=user.identity_provider,
        external_identity_id=user.oidc_subject,
        active=user.active,
        role=context.principal.role,
        development_identity=context.development_identity,
        organization_name=organization_name or "Institute",
        teams=[
            CurrentTeam(
                id=team.id,
                name=team.name,
                role=context.principal.team_roles[team.id],
            )
            for team in teams
        ],
        created_at=user.created_at,
        last_login_at=user.last_login_at,
    )
