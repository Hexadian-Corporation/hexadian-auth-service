from unittest.mock import MagicMock

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hexadian_auth_common.fastapi import (
    JWTAuthDependency,
    _stub_jwt_auth,
    register_exception_handlers,
)

from src.application.ports.inbound.auth_service import AuthService
from src.domain.models.token_response import TokenResponse
from src.domain.models.user import User
from src.infrastructure.adapters.inbound.api.auth_router import init_router, router

JWT_SECRET = "test-secret-key-for-middleware-tests"
JWT_ALGORITHM = "HS256"


def _make_token(
    sub: str = "user-1",
    username: str = "testuser",
    permissions: list[str] | None = None,
    **extra_claims: object,
) -> str:
    import time

    payload = {
        "sub": sub,
        "username": username,
        "permissions": permissions or [],
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        **extra_claims,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


@pytest.fixture()
def mock_auth_service() -> MagicMock:
    return MagicMock(spec=AuthService)


@pytest.fixture()
def client(mock_auth_service: MagicMock) -> TestClient:
    """Client with real JWT auth dependency (no overrides)."""
    init_router(mock_auth_service)
    app = FastAPI()
    jwt_auth = JWTAuthDependency(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
    app.dependency_overrides[_stub_jwt_auth] = jwt_auth
    register_exception_handlers(app)
    app.include_router(router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    return TestClient(app)


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_user(**overrides: object) -> User:
    defaults: dict = {
        "id": "user-1",
        "username": "testuser",
        "group_ids": [],
        "is_active": True,
        "rsi_handle": "TestPilot",
        "rsi_verified": False,
    }
    defaults.update(overrides)
    return User(**defaults)


# ---------------------------------------------------------------------------
# Public endpoints — should work without token
# ---------------------------------------------------------------------------


class TestPublicEndpoints:
    def test_health_no_token(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_register_no_token(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.register.return_value = _make_user()
        response = client.post(
            "/auth/register",
            json={"username": "testuser", "password": "pw", "rsi_handle": "TestPilot"},
        )
        assert response.status_code == 201

    def test_login_no_token(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.authenticate.return_value = TokenResponse(
            access_token="jwt", refresh_token="rt", expires_in=900
        )
        response = client.post("/auth/login", json={"username": "u", "password": "p"})
        assert response.status_code == 200

    def test_token_refresh_no_token(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.refresh_token.return_value = TokenResponse(
            access_token="jwt", refresh_token="rt", expires_in=900
        )
        response = client.post("/auth/token/refresh", json={"refresh_token": "old"})
        assert response.status_code == 200

    def test_token_revoke_no_token(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        response = client.post("/auth/token/revoke", json={"refresh_token": "tok"})
        assert response.status_code == 204

    def test_authorize_no_token(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        from src.domain.models.auth_code import AuthCode

        mock_auth_service.authorize.return_value = AuthCode(
            id="ac-1", code="code", user_id="u1", redirect_uri="http://localhost:3000/callback", state="s"
        )
        response = client.post(
            "/auth/authorize",
            json={"username": "u", "password": "p", "redirect_uri": "http://localhost:3000/callback", "state": "s"},
        )
        assert response.status_code == 200

    def test_token_exchange_no_token(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.exchange_code.return_value = TokenResponse(
            access_token="jwt", refresh_token="rt", expires_in=900
        )
        response = client.post(
            "/auth/token/exchange", json={"code": "code", "redirect_uri": "http://localhost:3000/callback"}
        )
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Protected endpoints — no token → 401
# ---------------------------------------------------------------------------


class TestProtectedEndpointsNoToken:
    def test_list_users_no_token_returns_401(self, client: TestClient) -> None:
        response = client.get("/auth/users")
        assert response.status_code == 401
        assert response.json()["detail"] == "Authentication required"

    def test_get_user_no_token_returns_401(self, client: TestClient) -> None:
        response = client.get("/auth/users/user-1")
        assert response.status_code == 401

    def test_delete_user_no_token_returns_401(self, client: TestClient) -> None:
        response = client.delete("/auth/users/user-1")
        assert response.status_code == 401

    def test_verify_start_no_token_returns_401(self, client: TestClient) -> None:
        response = client.post("/auth/verify/start?user_id=user-1", json={"rsi_handle": "TestPilot"})
        assert response.status_code == 401

    def test_verify_confirm_no_token_returns_401(self, client: TestClient) -> None:
        response = client.post("/auth/verify/confirm?user_id=user-1")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Protected endpoints — invalid token → 401
# ---------------------------------------------------------------------------


class TestProtectedEndpointsInvalidToken:
    def test_list_users_invalid_token_returns_401(self, client: TestClient) -> None:
        response = client.get("/auth/users", headers=_auth_header("bad-token"))
        assert response.status_code == 401

    def test_get_user_invalid_token_returns_401(self, client: TestClient) -> None:
        response = client.get("/auth/users/user-1", headers=_auth_header("bad-token"))
        assert response.status_code == 401

    def test_delete_user_invalid_token_returns_401(self, client: TestClient) -> None:
        response = client.delete("/auth/users/user-1", headers=_auth_header("bad-token"))
        assert response.status_code == 401

    def test_verify_start_invalid_token_returns_401(self, client: TestClient) -> None:
        response = client.post(
            "/auth/verify/start?user_id=user-1", json={"rsi_handle": "TestPilot"}, headers=_auth_header("bad-token")
        )
        assert response.status_code == 401

    def test_verify_confirm_invalid_token_returns_401(self, client: TestClient) -> None:
        response = client.post("/auth/verify/confirm?user_id=user-1", headers=_auth_header("bad-token"))
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Protected endpoints — wrong permissions → 403
# ---------------------------------------------------------------------------


class TestProtectedEndpointsWrongPermissions:
    def test_list_users_no_permission_returns_403(self, client: TestClient) -> None:
        token = _make_token(permissions=[])
        response = client.get("/auth/users", headers=_auth_header(token))
        assert response.status_code == 403
        assert "auth:users:read" in response.json()["detail"]

    def test_delete_user_no_admin_permission_returns_403(self, client: TestClient) -> None:
        token = _make_token(permissions=["auth:users:read"])
        response = client.delete("/auth/users/user-1", headers=_auth_header(token))
        assert response.status_code == 403
        assert "auth:users:admin" in response.json()["detail"]

    def test_get_user_other_user_no_permission_returns_403(self, client: TestClient) -> None:
        token = _make_token(sub="user-1", permissions=[])
        response = client.get("/auth/users/other-user", headers=_auth_header(token))
        assert response.status_code == 403
        assert "auth:users:read" in response.json()["detail"]


# ---------------------------------------------------------------------------
# Protected endpoints — correct permissions → success
# ---------------------------------------------------------------------------


class TestProtectedEndpointsCorrectPermissions:
    def test_list_users_with_read_permission(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.list_users.return_value = []
        token = _make_token(permissions=["auth:users:read"])
        response = client.get("/auth/users", headers=_auth_header(token))
        assert response.status_code == 200

    def test_delete_user_with_admin_permission(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        token = _make_token(permissions=["auth:users:admin"])
        response = client.delete("/auth/users/user-1", headers=_auth_header(token))
        assert response.status_code == 204

    def test_get_user_with_read_permission(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.get_user.return_value = _make_user(id="other-user")
        token = _make_token(sub="user-1", permissions=["auth:users:read"])
        response = client.get("/auth/users/other-user", headers=_auth_header(token))
        assert response.status_code == 200

    def test_verify_start_with_valid_token(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.start_verification.return_value = "code123"
        token = _make_token(permissions=[])
        response = client.post(
            "/auth/verify/start?user_id=user-1", json={"rsi_handle": "TestPilot"}, headers=_auth_header(token)
        )
        assert response.status_code == 200

    def test_verify_confirm_with_valid_token(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.confirm_verification.return_value = True
        token = _make_token(permissions=[])
        response = client.post("/auth/verify/confirm?user_id=user-1", headers=_auth_header(token))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Self-access pattern for GET /auth/users/{id}
# ---------------------------------------------------------------------------


class TestSelfAccessPattern:
    def test_user_can_view_own_profile_without_permission(
        self, client: TestClient, mock_auth_service: MagicMock
    ) -> None:
        mock_auth_service.get_user.return_value = _make_user(id="user-1")
        token = _make_token(sub="user-1", permissions=[])
        response = client.get("/auth/users/user-1", headers=_auth_header(token))
        assert response.status_code == 200

    def test_user_cannot_view_other_profile_without_permission(self, client: TestClient) -> None:
        token = _make_token(sub="user-1", permissions=[])
        response = client.get("/auth/users/other-user", headers=_auth_header(token))
        assert response.status_code == 403

    def test_user_can_view_other_profile_with_read_permission(
        self, client: TestClient, mock_auth_service: MagicMock
    ) -> None:
        mock_auth_service.get_user.return_value = _make_user(id="other-user")
        token = _make_token(sub="user-1", permissions=["auth:users:read"])
        response = client.get("/auth/users/other-user", headers=_auth_header(token))
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Exception handler JSON format
# ---------------------------------------------------------------------------


class TestExceptionHandlerFormat:
    def test_401_returns_json_detail(self, client: TestClient) -> None:
        response = client.get("/auth/users")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_403_returns_json_detail(self, client: TestClient) -> None:
        token = _make_token(permissions=[])
        response = client.get("/auth/users", headers=_auth_header(token))
        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)
