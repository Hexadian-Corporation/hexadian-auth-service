from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth

from src.application.ports.inbound.auth_service import AuthService
from src.domain.exceptions.user_exceptions import (
    InvalidAuthCodeError,
    InvalidCredentialsError,
    InvalidRedirectUriError,
    UserNotFoundError,
)
from src.domain.models.auth_code import AuthCode
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


class TestAuthorizeEndpoint:
    def test_authorize_returns_code_and_state(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.authorize.return_value = AuthCode(
            id="ac-1",
            code="auth-code-123",
            user_id="user-1",
            redirect_uri="http://localhost:3000/callback",
            state="state-xyz",
        )

        response = client.post(
            "/auth/authorize",
            json={
                "username": "user",
                "password": "pass",
                "redirect_uri": "http://localhost:3000/callback",
                "state": "state-xyz",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == "auth-code-123"
        assert data["state"] == "state-xyz"
        assert data["redirect_uri"] == "http://localhost:3000/callback"

    def test_authorize_invalid_credentials_returns_401(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.authorize.side_effect = InvalidCredentialsError()

        response = client.post(
            "/auth/authorize",
            json={
                "username": "user",
                "password": "wrong",
                "redirect_uri": "http://localhost:3000/callback",
            },
        )

        assert response.status_code == 401

    def test_authorize_invalid_redirect_uri_returns_400(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.authorize.side_effect = InvalidRedirectUriError("http://evil.com/callback")

        response = client.post(
            "/auth/authorize",
            json={
                "username": "user",
                "password": "pass",
                "redirect_uri": "http://evil.com/callback",
            },
        )

        assert response.status_code == 400

    def test_authorize_missing_fields_returns_422(self, client: TestClient) -> None:
        response = client.post("/auth/authorize", json={})

        assert response.status_code == 422

    def test_authorize_default_state_is_empty(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.authorize.return_value = AuthCode(
            id="ac-1",
            code="auth-code-123",
            user_id="user-1",
            redirect_uri="http://localhost:3000/callback",
            state="",
        )

        response = client.post(
            "/auth/authorize",
            json={
                "username": "user",
                "password": "pass",
                "redirect_uri": "http://localhost:3000/callback",
            },
        )

        assert response.status_code == 200
        assert response.json()["state"] == ""
        mock_auth_service.authorize.assert_called_once_with("user", "pass", "http://localhost:3000/callback", "")


class TestTokenExchangeEndpoint:
    def test_exchange_returns_token_response(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.exchange_code.return_value = TokenResponse(
            access_token="jwt-access-token",
            refresh_token="uuid-refresh-token",
            expires_in=900,
        )

        response = client.post(
            "/auth/token/exchange",
            json={"code": "auth-code-123", "redirect_uri": "http://localhost:3000/callback"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "jwt-access-token"
        assert data["refresh_token"] == "uuid-refresh-token"
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 900

    def test_exchange_invalid_code_returns_400(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.exchange_code.side_effect = InvalidAuthCodeError()

        response = client.post(
            "/auth/token/exchange",
            json={"code": "bad-code", "redirect_uri": "http://localhost:3000/callback"},
        )

        assert response.status_code == 400

    def test_exchange_user_not_found_returns_400(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.exchange_code.side_effect = UserNotFoundError("deleted-user")

        response = client.post(
            "/auth/token/exchange",
            json={"code": "auth-code-123", "redirect_uri": "http://localhost:3000/callback"},
        )

        assert response.status_code == 400

    def test_exchange_missing_fields_returns_422(self, client: TestClient) -> None:
        response = client.post("/auth/token/exchange", json={})

        assert response.status_code == 422
