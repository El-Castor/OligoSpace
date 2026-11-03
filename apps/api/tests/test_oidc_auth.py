from __future__ import annotations

import time
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock
from urllib.parse import parse_qs

import httpx
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from oligospace_api.core.config import Settings
from oligospace_api.models.enums import GlobalRole
from oligospace_api.models.registry import User
from oligospace_api.security import auth


@pytest.mark.parametrize(
    "roles", ["not-admin", {"admin": True}, ["admin", None], ["admin", 1], None, 1]
)
def test_malformed_role_claims_cannot_grant_privileges(roles: object) -> None:
    assert auth._role_from_claims({"realm_access": {"roles": roles}}) is GlobalRole.VIEWER


def test_role_names_require_exact_values() -> None:
    assert auth._role_from_claims({"realm_access": {"roles": ["not-admin"]}}) is GlobalRole.VIEWER


@pytest.fixture
def oidc_settings() -> Settings:
    return Settings(
        environment="test",
        auth_mode="oidc",
        oidc_issuer="https://identity.example/realms/test",
        oidc_client_secret="synthetic-test-secret",
    )


@pytest.fixture
def signing_key(monkeypatch: pytest.MonkeyPatch) -> rsa.RSAPrivateKey:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(
        auth,
        "PyJWKClient",
        lambda url: SimpleNamespace(
            get_signing_key_from_jwt=lambda token: SimpleNamespace(key=key.public_key())
        ),
    )
    return key


def signed_token(key: rsa.RSAPrivateKey, **overrides: object) -> str:
    claims = {
        "iss": "https://identity.example/realms/test",
        "aud": "oligospace-api",
        "sub": "synthetic-subject",
        "iat": int(time.time()) - 10,
        "exp": int(time.time()) + 300,
        "realm_access": {"roles": ["admin"]},
    }
    claims.update(overrides)
    return jwt.encode(claims, key, algorithm="RS256")


def provider_response(monkeypatch: pytest.MonkeyPatch, response: object) -> list[httpx.Request]:
    requests: list[httpx.Request] = []
    client = httpx.AsyncClient
    monkeypatch.setattr(auth, "httpx", httpx, raising=False)

    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if isinstance(response, Exception):
            raise response
        if isinstance(response, httpx.Response):
            return response
        return httpx.Response(200, json=response)

    def build_client(**kwargs: object) -> httpx.AsyncClient:
        assert 0 < float(kwargs["timeout"]) <= 10
        return client(transport=httpx.MockTransport(handle), **kwargs)

    monkeypatch.setattr(auth.httpx, "AsyncClient", build_client)
    return requests


def local_user(provider: str = "keycloak", *, active: bool = True) -> User:
    return User(
        id=uuid.uuid4(),
        organization_id=uuid.uuid4(),
        oidc_subject="synthetic-subject",
        identity_provider=provider,
        email="synthetic@example.test",
        display_name="Synthetic",
        global_role=GlobalRole.MEMBER,
        active=active,
    )


def local_session(user: User | None) -> AsyncMock:
    session = AsyncMock()
    session.scalar.return_value = user
    session.execute.return_value = SimpleNamespace(all=lambda: [])
    return session


async def authenticate(token: str, settings: Settings, session: AsyncMock) -> auth.AuthContext:
    return await auth.get_auth_context(
        credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
        development_user=None,
        development_auth=None,
        session=session,
        settings=settings,
    )


@pytest.mark.parametrize("secret", ["", "   "])
def test_oidc_runtime_requires_confidential_client_secret(secret: str) -> None:
    with pytest.raises(ValueError, match="OIDC_CLIENT_SECRET"):
        Settings(environment="test", auth_mode="oidc", oidc_client_secret=secret).validate_runtime()


@pytest.mark.parametrize(
    "response",
    [
        {"active": False},
        {},
        {"active": "true"},
        {"active": 1},
        [],
        httpx.Response(503),
        httpx.Response(200, content=b"not-json"),
        httpx.ConnectError("synthetic outage"),
        httpx.ReadTimeout("synthetic timeout"),
    ],
)
async def test_provider_inactive_or_unavailable_denies_unexpired_signed_token(
    monkeypatch: pytest.MonkeyPatch,
    oidc_settings: Settings,
    signing_key: rsa.RSAPrivateKey,
    response: object,
) -> None:
    provider_response(monkeypatch, response)
    session = local_session(local_user())
    with pytest.raises(HTTPException) as error:
        await authenticate(signed_token(signing_key), oidc_settings, session)
    assert error.value.status_code == 401
    session.scalar.assert_not_awaited()


async def test_provider_checked_every_request_and_legacy_identity_bound_after_validation(
    monkeypatch: pytest.MonkeyPatch,
    oidc_settings: Settings,
    signing_key: rsa.RSAPrivateKey,
) -> None:
    requests = provider_response(monkeypatch, {"active": True})
    user = local_user()
    session = local_session(user)
    token = signed_token(signing_key)
    first = await authenticate(token, oidc_settings, session)
    second = await authenticate(token, oidc_settings, session)
    assert first.principal.role == second.principal.role == GlobalRole.MEMBER
    assert user.identity_provider == "https://identity.example/realms/test"
    assert len(requests) == 2
    assert requests[0].url == (
        "https://identity.example/realms/test/protocol/openid-connect/token/introspect"
    )
    body = parse_qs(requests[0].content.decode())
    valid_credentials = body == {
        "token": [token],
        "client_id": ["oligospace-web"],
        "client_secret": ["synthetic-test-secret"],
    }
    assert valid_credentials


async def test_unknown_provider_rejected_before_profile_mutation(
    monkeypatch: pytest.MonkeyPatch,
    oidc_settings: Settings,
    signing_key: rsa.RSAPrivateKey,
) -> None:
    provider_response(monkeypatch, {"active": True})
    user = local_user("https://other.example/realms/other")
    with pytest.raises(HTTPException) as error:
        await authenticate(
            signed_token(signing_key, email="changed@example.test"),
            oidc_settings,
            local_session(user),
        )
    assert error.value.status_code == 403
    assert user.identity_provider == "https://other.example/realms/other"
    assert user.email == "synthetic@example.test"


@pytest.mark.parametrize("active,provisioned", [(False, True), (True, False)])
async def test_local_disabled_or_unprovisioned_denied(
    monkeypatch: pytest.MonkeyPatch,
    oidc_settings: Settings,
    signing_key: rsa.RSAPrivateKey,
    active: bool,
    provisioned: bool,
) -> None:
    provider_response(monkeypatch, {"active": True})
    user = local_user(active=active) if provisioned else None
    with pytest.raises(HTTPException) as error:
        await authenticate(signed_token(signing_key), oidc_settings, local_session(user))
    assert error.value.status_code == 403


@pytest.mark.parametrize(
    "overrides",
    [
        {"iss": "https://wrong.example"},
        {"aud": "other-api"},
        {"exp": 1},
        {"iat": int(time.time()) + 3600},
        {"iat": "invalid"},
        {"sub": 1},
        {"sub": ""},
        {"sub": "   "},
        {"sub": None},
    ],
)
def test_invalid_claims_rejected(
    oidc_settings: Settings,
    signing_key: rsa.RSAPrivateKey,
    overrides: dict[str, object],
) -> None:
    with pytest.raises(HTTPException) as error:
        auth._decode_token(signed_token(signing_key, **overrides), oidc_settings)
    assert error.value.status_code == 401


def test_invalid_signature_rejected(
    oidc_settings: Settings,
    signing_key: rsa.RSAPrivateKey,
) -> None:
    other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    with pytest.raises(HTTPException) as error:
        auth._decode_token(signed_token(other_key), oidc_settings)
    assert error.value.status_code == 401


@pytest.mark.parametrize("missing", ["iss", "aud", "exp", "iat", "sub"])
def test_required_claims_rejected(
    oidc_settings: Settings,
    signing_key: rsa.RSAPrivateKey,
    missing: str,
) -> None:
    claims = jwt.decode(signed_token(signing_key), options={"verify_signature": False})
    del claims[missing]
    token = jwt.encode(claims, signing_key, algorithm="RS256")
    with pytest.raises(HTTPException) as error:
        auth._decode_token(token, oidc_settings)
    assert error.value.status_code == 401


async def test_provider_revocation_denies_next_request_with_same_unexpired_token(
    monkeypatch: pytest.MonkeyPatch,
    oidc_settings: Settings,
    signing_key: rsa.RSAPrivateKey,
) -> None:
    response = {"active": True}
    provider_response(monkeypatch, response)
    session = local_session(local_user())
    token = signed_token(signing_key)
    await authenticate(token, oidc_settings, session)
    response["active"] = False
    with pytest.raises(HTTPException) as error:
        await authenticate(token, oidc_settings, session)
    assert error.value.status_code == 401
    assert session.scalar.await_count == 1


async def test_invalid_crypto_rejected_before_provider_or_database_access(
    monkeypatch: pytest.MonkeyPatch,
    oidc_settings: Settings,
    signing_key: rsa.RSAPrivateKey,
) -> None:
    requests = provider_response(monkeypatch, {"active": True})
    session = local_session(local_user())
    with pytest.raises(HTTPException) as error:
        await authenticate(signed_token(signing_key, exp=1), oidc_settings, session)
    assert error.value.status_code == 401
    assert not requests
    session.scalar.assert_not_awaited()


async def test_local_role_and_memberships_reloaded_for_same_token(
    monkeypatch: pytest.MonkeyPatch,
    oidc_settings: Settings,
    signing_key: rsa.RSAPrivateKey,
) -> None:
    provider_response(monkeypatch, {"active": True})
    user = local_user()
    session = local_session(user)
    project_id = uuid.uuid4()
    token = signed_token(signing_key)
    session.execute.side_effect = [
        SimpleNamespace(all=lambda: []),
        SimpleNamespace(all=lambda: [(project_id, "viewer")]),
        SimpleNamespace(all=lambda: []),
        SimpleNamespace(all=lambda: []),
    ]
    first = await authenticate(token, oidc_settings, session)
    user.global_role = GlobalRole.VIEWER
    second = await authenticate(token, oidc_settings, session)
    assert first.principal.role is GlobalRole.MEMBER
    assert second.principal.role is GlobalRole.VIEWER
    assert project_id in first.principal.project_roles
    assert project_id not in second.principal.project_roles


@pytest.mark.parametrize(
    "exception_type,rule",
    [
        (jwt.PyJWKClientConnectionError, "JWKS_FETCH_FAILED"),
        (jwt.InvalidSignatureError, "JWT_SIGNATURE_INVALID"),
        (jwt.InvalidAudienceError, "JWT_CLAIMS_INVALID"),
    ],
)
def test_decode_warnings_classify_failure_without_sensitive_details(
    monkeypatch: pytest.MonkeyPatch,
    oidc_settings: Settings,
    caplog: pytest.LogCaptureFixture,
    exception_type: type[Exception],
    rule: str,
) -> None:
    def reject(token: str) -> None:
        raise exception_type("synthetic-sensitive-exception-detail")

    monkeypatch.setattr(
        auth,
        "PyJWKClient",
        lambda url: SimpleNamespace(
            get_signing_key_from_jwt=reject,
        ),
    )
    with pytest.raises(HTTPException) as error:
        auth._decode_token("synthetic-sensitive-bearer", oidc_settings)
    assert error.value.status_code == 401
    records = [record for record in caplog.records if record.name == auth.__name__]
    assert [record.getMessage() for record in records] == [rule]
    assert all(record.exc_info is None and not record.args for record in records)
    assert "synthetic-sensitive" not in caplog.text
    assert oidc_settings.oidc_client_secret not in caplog.text


@pytest.mark.parametrize(
    "response,rule",
    [
        (httpx.Response(503), "OIDC_INTROSPECTION_HTTP_FAILED"),
        (
            httpx.ConnectError("synthetic-sensitive-exception-detail"),
            "OIDC_INTROSPECTION_TRANSPORT_FAILED",
        ),
        (
            httpx.Response(200, content=b"synthetic-sensitive-body"),
            "OIDC_INTROSPECTION_JSON_INVALID",
        ),
        ({"active": False}, "OIDC_INTROSPECTION_INACTIVE"),
    ],
)
async def test_introspection_warnings_classify_failure_without_sensitive_details(
    monkeypatch: pytest.MonkeyPatch,
    oidc_settings: Settings,
    caplog: pytest.LogCaptureFixture,
    response: object,
    rule: str,
) -> None:
    provider_response(monkeypatch, response)
    with pytest.raises(HTTPException) as error:
        await auth._require_active_token("synthetic-sensitive-bearer", oidc_settings)
    assert error.value.status_code == 401
    records = [record for record in caplog.records if record.name == auth.__name__]
    assert [record.getMessage() for record in records] == [rule]
    assert all(record.exc_info is None and not record.args for record in records)
    assert "synthetic-sensitive" not in caplog.text
    assert oidc_settings.oidc_client_secret not in caplog.text
