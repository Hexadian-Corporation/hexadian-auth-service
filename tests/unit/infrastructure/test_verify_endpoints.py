from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth

from src.application.ports.inbound.auth_service import AuthService
from src.domain.exceptions.app_signature_exceptions import InvalidAppSignatureError
from src.domain.exceptions.user_exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
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
            permissions=["users:read", "users:admin"],
        )

    app.dependency_overrides[_stub_jwt_auth] = _mock_jwt_auth
    return TestClient(app)


class TestVerifyStartEndpoint:
    def test_start_verification_success(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.start_verification.return_value = "abc123code"

        response = client.post("/auth/verify/start?user_id=user-1", json={"rsi_handle": "TestPilot"})

        assert response.status_code == 200
        data = response.json()
        assert data["verification_code"] == "abc123code"
        assert data["verified"] is False
        assert "instructions" in data["message"].lower() or "bio" in data["message"].lower()

    def test_start_verification_invalid_handle_format(self, client: TestClient) -> None:
        response = client.post("/auth/verify/start?user_id=user-1", json={"rsi_handle": "ab"})

        assert response.status_code == 422

    def test_start_verification_user_not_found(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.start_verification.side_effect = UserNotFoundError("user-1")

        response = client.post("/auth/verify/start?user_id=user-1", json={"rsi_handle": "TestPilot"})

        assert response.status_code == 404

    def test_start_verification_value_error(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.start_verification.side_effect = ValueError("Invalid")

        response = client.post("/auth/verify/start?user_id=user-1", json={"rsi_handle": "TestPilot"})

        assert response.status_code == 400


class TestVerifyConfirmEndpoint:
    def test_confirm_verification_success(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.confirm_verification.return_value = True

        response = client.post("/auth/verify/confirm?user_id=user-1")

        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is True

    def test_confirm_verification_not_verified(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.confirm_verification.return_value = False

        response = client.post("/auth/verify/confirm?user_id=user-1")

        assert response.status_code == 200
        data = response.json()
        assert data["verified"] is False
        assert "not found" in data["message"].lower()

    def test_confirm_verification_user_not_found(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.confirm_verification.side_effect = UserNotFoundError("user-1")

        response = client.post("/auth/verify/confirm?user_id=user-1")

        assert response.status_code == 404

    def test_confirm_verification_not_started(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.confirm_verification.side_effect = ValueError("Verification not started")

        response = client.post("/auth/verify/confirm?user_id=user-1")

        assert response.status_code == 400


class TestRegisterEndpoint:
    def test_register_duplicate_username_returns_409_with_field(
        self, client: TestClient, mock_auth_service: MagicMock
    ) -> None:
        mock_auth_service.register.side_effect = UserAlreadyExistsError("taken", field="username")

        response = client.post(
            "/auth/register",
            json={"username": "taken", "password": "pw", "rsi_handle": "TakenPilot"},
        )

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["field"] == "username"
        assert data["detail"]["message"] == "Username already taken"

    def test_register_duplicate_rsi_handle_returns_409_with_field(
        self, client: TestClient, mock_auth_service: MagicMock
    ) -> None:
        mock_auth_service.register.side_effect = UserAlreadyExistsError("TakenPilot", field="rsi_handle")

        response = client.post(
            "/auth/register",
            json={"username": "newuser", "password": "pw", "rsi_handle": "TakenPilot"},
        )

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["field"] == "rsi_handle"
        assert data["detail"]["message"] == "RSI handle already registered"

    def test_register_invalid_rsi_handle_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/auth/register",
            json={"username": "user", "password": "pw", "rsi_handle": "ab"},
        )

        assert response.status_code == 422

    def test_register_missing_rsi_handle_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/auth/register",
            json={"username": "user", "password": "pw"},
        )

        assert response.status_code == 422

    def test_register_invalid_app_signature_returns_403(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.register.side_effect = InvalidAppSignatureError()

        response = client.post(
            "/auth/register",
            json={
                "username": "user",
                "password": "pw",
                "rsi_handle": "ValidPilot",
                "app_id": "hhh-frontend",
                "app_signature": "bad-sig",
            },
        )

        assert response.status_code == 403

    def test_register_with_app_id_passes_to_service(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        from src.domain.models.user import User

        mock_auth_service.register.return_value = User(id="u-1", username="newuser", rsi_handle="ValidPilot")

        response = client.post(
            "/auth/register",
            json={
                "username": "newuser",
                "password": "pw",
                "rsi_handle": "ValidPilot",
                "app_id": "hhh-frontend",
                "app_signature": "some-sig",
            },
        )

        assert response.status_code == 201
        mock_auth_service.register.assert_called_once_with("newuser", "pw", "ValidPilot", "hhh-frontend", "some-sig")


class TestLoginEndpoint:
    def test_login_invalid_credentials_returns_401(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.authenticate.side_effect = InvalidCredentialsError()

        response = client.post("/auth/login", json={"username": "u", "password": "wrong"})

        assert response.status_code == 401


class TestGetUserEndpoint:
    def test_get_user_not_found_returns_404(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.get_user.side_effect = UserNotFoundError("missing")

        response = client.get("/auth/users/missing")

        assert response.status_code == 404


class TestDeleteUserEndpoint:
    def test_delete_user_not_found_returns_404(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.delete_user.side_effect = UserNotFoundError("gone")

        response = client.delete("/auth/users/gone")

        assert response.status_code == 404
