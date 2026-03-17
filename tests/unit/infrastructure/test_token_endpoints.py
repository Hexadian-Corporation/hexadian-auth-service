from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth

from src.application.ports.inbound.auth_service import AuthService
from src.domain.exceptions.user_exceptions import (
    InvalidCredentialsError,
    RefreshTokenNotFoundError,
    UserNotFoundError,
)
from src.domain.models.token_response import TokenResponse
from src.infrastructure.adapters.inbound.api.auth_router import init_router, router


@pytest.fixture()
def mock_auth_service() -> MagicMock:
    return MagicMock(spec=AuthService)


@pytest.fixture()
def client(mock_auth_service: MagicMock) -> TestClient:
    from fastapi import FastAPI

    init_router(mock_auth_service)
    app = FastAPI()
    app.include_router(router)

    async def _mock_jwt_auth() -> UserContext:
        return UserContext(
            user_id="user-1",
            username="testuser",
            permissions=["auth:users:read", "auth:users:admin"],
        )

    app.dependency_overrides[_stub_jwt_auth] = _mock_jwt_auth
    return TestClient(app)


class TestLoginEndpointTokenResponse:
    def test_login_returns_token_response(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.authenticate.return_value = TokenResponse(
            access_token="jwt-access-token",
            refresh_token="uuid-refresh-token",
            expires_in=900,
        )

        response = client.post("/auth/login", json={"username": "user", "password": "pass"})

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "jwt-access-token"
        assert data["refresh_token"] == "uuid-refresh-token"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900

    def test_login_invalid_credentials_returns_401(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.authenticate.side_effect = InvalidCredentialsError()

        response = client.post("/auth/login", json={"username": "u", "password": "wrong"})

        assert response.status_code == 401


class TestRefreshTokenEndpoint:
    def test_refresh_token_success(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.refresh_token.return_value = TokenResponse(
            access_token="new-jwt",
            refresh_token="new-refresh",
            expires_in=900,
        )

        response = client.post("/auth/token/refresh", json={"refresh_token": "old-refresh"})

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "new-jwt"
        assert data["refresh_token"] == "new-refresh"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900

    def test_refresh_token_not_found_returns_401(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.refresh_token.side_effect = RefreshTokenNotFoundError("bad-token")

        response = client.post("/auth/token/refresh", json={"refresh_token": "bad-token"})

        assert response.status_code == 401

    def test_refresh_token_user_not_found_returns_401(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.refresh_token.side_effect = UserNotFoundError("deleted-user")

        response = client.post("/auth/token/refresh", json={"refresh_token": "orphaned-token"})

        assert response.status_code == 401

    def test_refresh_token_missing_body_returns_422(self, client: TestClient) -> None:
        response = client.post("/auth/token/refresh", json={})

        assert response.status_code == 422


class TestRevokeTokenEndpoint:
    def test_revoke_token_success_returns_204(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        response = client.post("/auth/token/revoke", json={"refresh_token": "token-to-revoke"})

        assert response.status_code == 204
        mock_auth_service.revoke_token.assert_called_once_with("token-to-revoke")

    def test_revoke_token_not_found_returns_401(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.revoke_token.side_effect = RefreshTokenNotFoundError("bad-token")

        response = client.post("/auth/token/revoke", json={"refresh_token": "bad-token"})

        assert response.status_code == 401

    def test_revoke_token_missing_body_returns_422(self, client: TestClient) -> None:
        response = client.post("/auth/token/revoke", json={})

        assert response.status_code == 422
