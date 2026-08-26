from fastapi import APIRouter, Depends

from oligospace_api.schemas.auth import CurrentUser
from oligospace_api.security.auth import AuthContext, get_auth_context

router = APIRouter(prefix="/me", tags=["identity"])


@router.get("", response_model=CurrentUser)
async def current_user(context: AuthContext = Depends(get_auth_context)) -> CurrentUser:
    return CurrentUser(
        id=context.principal.user_id,
        organization_id=context.principal.organization_id,
        email=context.email,
        display_name=context.display_name,
        role=context.principal.role,
        development_identity=context.development_identity,
    )
