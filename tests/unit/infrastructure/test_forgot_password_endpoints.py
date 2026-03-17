from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth

from src.application.ports.inbound.auth_service import AuthService
from src.domain.exceptions.user_exceptions import (
    RsiHandleMismatchError,
    UserNotFoundError,
)
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


class TestForgotPasswordEndpoint:
    def test_forgot_password_success(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.forgot_password.return_value = "verification-code-123"

        response = client.post(
            "/auth/password/forgot",
            json={"username": "testuser", "rsi_handle": "TestPilot"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["verification_code"] == "verification-code-123"
        assert "message" in data

    def test_forgot_password_user_not_found(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.forgot_password.side_effect = UserNotFoundError("testuser")

        response = client.post(
            "/auth/password/forgot",
            json={"username": "testuser", "rsi_handle": "TestPilot"},
        )

        assert response.status_code == 404

    def test_forgot_password_rsi_handle_mismatch(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.forgot_password.side_effect = RsiHandleMismatchError("testuser")

        response = client.post(
            "/auth/password/forgot",
            json={"username": "testuser", "rsi_handle": "WrongHandle"},
        )

        assert response.status_code == 400

    def test_forgot_password_invalid_rsi_handle_format(self, client: TestClient) -> None:
        response = client.post(
            "/auth/password/forgot",
            json={"username": "testuser", "rsi_handle": "ab"},
        )

        assert response.status_code == 422


class TestForgotPasswordConfirmEndpoint:
    def test_confirm_forgot_password_success(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.confirm_forgot_password.return_value = None

        response = client.post(
            "/auth/password/forgot-confirm",
            json={"username": "testuser", "rsi_handle": "TestPilot", "new_password": "new-secure-password"},
        )

        assert response.status_code == 204

    def test_confirm_forgot_password_user_not_found(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.confirm_forgot_password.side_effect = UserNotFoundError("testuser")

        response = client.post(
            "/auth/password/forgot-confirm",
            json={"username": "testuser", "rsi_handle": "TestPilot", "new_password": "new-secure-password"},
        )

        assert response.status_code == 404

    def test_confirm_forgot_password_rsi_handle_mismatch(
        self, client: TestClient, mock_auth_service: MagicMock
    ) -> None:
        mock_auth_service.confirm_forgot_password.side_effect = RsiHandleMismatchError("testuser")

        response = client.post(
            "/auth/password/forgot-confirm",
            json={"username": "testuser", "rsi_handle": "WrongHandle", "new_password": "new-secure-password"},
        )

        assert response.status_code == 400

    def test_confirm_forgot_password_no_verification_code(
        self, client: TestClient, mock_auth_service: MagicMock
    ) -> None:
        mock_auth_service.confirm_forgot_password.side_effect = ValueError("No verification code set")

        response = client.post(
            "/auth/password/forgot-confirm",
            json={"username": "testuser", "rsi_handle": "TestPilot", "new_password": "new-secure-password"},
        )

        assert response.status_code == 400

    def test_confirm_forgot_password_code_not_in_bio(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.confirm_forgot_password.side_effect = ValueError("Verification code not found")

        response = client.post(
            "/auth/password/forgot-confirm",
            json={"username": "testuser", "rsi_handle": "TestPilot", "new_password": "new-secure-password"},
        )

        assert response.status_code == 400

    def test_confirm_forgot_password_invalid_rsi_handle_format(self, client: TestClient) -> None:
        response = client.post(
            "/auth/password/forgot-confirm",
            json={"username": "testuser", "rsi_handle": "ab", "new_password": "new-secure-password"},
        )

        assert response.status_code == 422

    def test_confirm_forgot_password_short_password(self, client: TestClient) -> None:
        response = client.post(
            "/auth/password/forgot-confirm",
            json={"username": "testuser", "rsi_handle": "TestPilot", "new_password": "short"},
        )

        assert response.status_code == 422
