import hashlib
import hmac

import pytest

from oligospace_api.core.config import Settings
from oligospace_api.models.enums import GlobalRole
from oligospace_api.security.auth import _role_from_claims, development_signature


def test_development_signature_is_bound_to_user_and_secret() -> None:
    user_id = "00000000-0000-0000-0000-000000000001"
    secret = "integration-secret"
    expected = hmac.new(secret.encode(), user_id.encode(), hashlib.sha256).hexdigest()

    assert development_signature(user_id, secret) == expected
    assert development_signature(user_id, "another-secret") != expected


def test_oidc_roles_default_to_viewer_and_select_strongest_known_role() -> None:
    assert _role_from_claims({}) is GlobalRole.VIEWER
    assert (
        _role_from_claims({"realm_access": {"roles": ["member", "team_manager"]}})
        is GlobalRole.TEAM_MANAGER
    )
    assert _role_from_claims({"realm_access": {"roles": ["viewer", "admin"]}}) is GlobalRole.ADMIN


def test_production_rejects_development_auth_mode() -> None:
    settings = Settings(
        environment="production",
        auth_mode="development",
        database_url="postgresql+asyncpg://oligospace:strong-password@postgres/oligospace",
    )
    with pytest.raises(ValueError, match="AUTH_MODE must be oidc"):
        settings.validate_runtime()
