from __future__ import annotations

import hashlib
import hmac
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import cast

import jwt
from fastapi import Depends, Header, HTTPException, status
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


def development_signature(user_id: str, secret: str) -> str:
    return hmac.new(secret.encode(), user_id.encode(), hashlib.sha256).hexdigest()


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
    development_user: str | None = Header(default=None, alias="X-OligoSpace-Development-User"),
    development_auth: str | None = Header(default=None, alias="X-OligoSpace-Development-Auth"),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> AuthContext:
    if settings.auth_mode == "development":
        if development_user is None or development_auth is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "development_session_required",
                    "message": "An explicit development session is required.",
                },
            )
        expected = development_signature(development_user, settings.development_auth_secret)
        if not hmac.compare_digest(expected, development_auth):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_development_session", "message": "Session rejected."},
            )
        try:
            development_user_id = uuid.UUID(development_user)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_development_session", "message": "Session rejected."},
            ) from exc
        user = await session.scalar(
            select(User).where(
                User.id == development_user_id,
                User.organization_id == settings.development_organization_id,
            )
        )
        return await _context_for_user(session, user, development_identity=True)

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "authentication_required", "message": "Bearer token required."},
            headers={"WWW-Authenticate": "Bearer"},
        )
    claims = _decode_token(credentials.credentials, settings)
    subject = str(claims["sub"])
    user = await session.scalar(select(User).where(User.oidc_subject == subject))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "account_not_provisioned", "message": "Account is not active."},
        )
    if not user.active:
        raise _disabled_account()

    user.identity_provider = str(settings.oidc_issuer).rstrip("/")
    user.email = str(claims.get("email") or user.email)
    user.display_name = str(claims.get("name") or user.display_name)
    user.first_name = str(claims["given_name"]) if claims.get("given_name") else user.first_name
    user.last_name = str(claims["family_name"]) if claims.get("family_name") else user.last_name
    claimed_role = _role_from_claims(claims)
    # The more restrictive role wins until explicit role-mapping policy is configured.
    role_order = {
        GlobalRole.VIEWER: 0,
        GlobalRole.MEMBER: 1,
        GlobalRole.TEAM_MANAGER: 2,
        GlobalRole.ADMIN: 3,
    }
    role = min((claimed_role, user.global_role), key=lambda candidate: role_order[candidate])
    return await _context_for_user(session, user, development_identity=False, effective_role=role)


def _disabled_account() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"code": "account_disabled", "message": "This account is disabled."},
    )


async def _context_for_user(
    session: AsyncSession,
    user: User | None,
    *,
    development_identity: bool,
    effective_role: GlobalRole | None = None,
) -> AuthContext:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "account_not_provisioned", "message": "Account is not provisioned."},
        )
    if not user.active:
        raise _disabled_account()

    team_rows = (
        await session.execute(
            select(TeamMembership.team_id, TeamMembership.role).where(
                TeamMembership.user_id == user.id
            )
        )
    ).all()
    project_rows = (
        await session.execute(
            select(ProjectMembership.project_id, ProjectMembership.role).where(
                ProjectMembership.user_id == user.id
            )
        )
    ).all()
    team_roles = {team_id: role for team_id, role in team_rows}
    project_roles = {project_id: role for project_id, role in project_rows}

    now = datetime.now(UTC)
    if user.last_login_at is None or user.last_login_at < now - timedelta(minutes=15):
        user.last_login_at = now
        await session.commit()
        await session.refresh(user)

    return AuthContext(
        principal=Principal(
            user.id,
            user.organization_id,
            effective_role or user.global_role,
            frozenset(team_roles),
            frozenset(project_roles),
            team_roles,
            project_roles,
        ),
        user=user,
        email=user.email,
        display_name=user.display_name,
        development_identity=development_identity,
    )
