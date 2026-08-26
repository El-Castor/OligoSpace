from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from oligospace_api.core.config import Settings, get_settings
from oligospace_api.db.session import get_session
from oligospace_api.domain.permissions import Principal
from oligospace_api.models.enums import GlobalRole
from oligospace_api.models.registry import ProjectMembership, TeamMembership, User

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    principal: Principal
    user: User | None
    email: str
    display_name: str
    development_identity: bool


def _role_from_claims(claims: dict[str, object]) -> GlobalRole:
    realm_access = claims.get("realm_access")
    roles = realm_access.get("roles", []) if isinstance(realm_access, dict) else []
    for role in (
        GlobalRole.ADMIN,
        GlobalRole.TEAM_MANAGER,
        GlobalRole.MEMBER,
        GlobalRole.VIEWER,
    ):
        if role.value in roles:
            return role
    return GlobalRole.VIEWER


def _decode_token(token: str, settings: Settings) -> dict[str, object]:
    try:
        signing_key = PyJWKClient(settings.oidc_jwks_url).get_signing_key_from_jwt(token)
        return cast(
            dict[str, object],
            jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience=settings.oidc_audience,
                issuer=str(settings.oidc_issuer).rstrip("/"),
                options={"require": ["exp", "iat", "sub"]},
            ),
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_token", "message": "The access token is invalid."},
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


async def get_auth_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuthContext:
    if settings.auth_mode == "development":
        principal = Principal(
            user_id=settings.development_user_id,
            organization_id=settings.development_organization_id,
            role=GlobalRole.ADMIN,
        )
        return AuthContext(
            principal=principal,
            user=None,
            email=settings.development_email,
            display_name=settings.development_display_name,
            development_identity=True,
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "authentication_required", "message": "Bearer token required."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = _decode_token(credentials.credentials, settings)
    subject = str(claims["sub"])
    user = await session.scalar(select(User).where(User.oidc_subject == subject))
    if user is None or not user.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "account_not_provisioned", "message": "Account is not active."},
        )

    team_ids = frozenset(
        (
            await session.scalars(
                select(TeamMembership.team_id).where(TeamMembership.user_id == user.id)
            )
        ).all()
    )
    project_ids = frozenset(
        (
            await session.scalars(
                select(ProjectMembership.project_id).where(ProjectMembership.user_id == user.id)
            )
        ).all()
    )
    claimed_role = _role_from_claims(claims)
    # The more restrictive role wins until explicit role-mapping policy is configured.
    role_order = {
        GlobalRole.VIEWER: 0,
        GlobalRole.MEMBER: 1,
        GlobalRole.TEAM_MANAGER: 2,
        GlobalRole.ADMIN: 3,
    }
    role = min((claimed_role, user.global_role), key=lambda candidate: role_order[candidate])
    return AuthContext(
        principal=Principal(user.id, user.organization_id, role, team_ids, project_ids),
        user=user,
        email=user.email,
        display_name=user.display_name,
        development_identity=False,
    )
