from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth

from src.application.ports.inbound.auth_service import AuthService
from src.domain.exceptions.user_exceptions import (
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.domain.models.user import User
from src.infrastructure.adapters.inbound.api.auth_router import init_router, router


@pytest.fixture()
def mock_auth_service() -> MagicMock:
    return MagicMock(spec=AuthService)


def _make_client(mock_auth_service: MagicMock, user_id: str, permissions: list[str]) -> TestClient:
    from fastapi import FastAPI

    init_router(mock_auth_service)
    app = FastAPI()
    app.include_router(router)

    async def _mock_jwt_auth() -> UserContext:
        return UserContext(
            user_id=user_id,
            username="testuser",
            permissions=permissions,
        )

    app.dependency_overrides[_stub_jwt_auth] = _mock_jwt_auth
    return TestClient(app)


@pytest.fixture()
def client(mock_auth_service: MagicMock) -> TestClient:
    return _make_client(mock_auth_service, "user-1", ["users:read", "users:admin"])


@pytest.fixture()
def regular_client(mock_auth_service: MagicMock) -> TestClient:
    return _make_client(mock_auth_service, "user-1", ["users:read"])


class TestUpdateUserSelfEdit:
    def test_self_edit_username_success(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.update_user.return_value = User(
            id="user-1", username="newname", rsi_handle="Pilot", rsi_verified=True
        )

        response = client.put("/auth/users/user-1", json={"username": "newname"})

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "newname"
        mock_auth_service.update_user.assert_called_once_with("user-1", {"username": "newname"})

    def test_self_edit_without_admin_permission(self, regular_client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.update_user.return_value = User(id="user-1", username="newname", rsi_handle="Pilot")

        response = regular_client.put("/auth/users/user-1", json={"username": "newname"})

        assert response.status_code == 200


class TestUpdateUserAdminEdit:
    def test_admin_edit_another_user_rsi_handle(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.update_user.return_value = User(
            id="user-2", username="other", rsi_handle="NewHandle", rsi_verified=False
        )

        response = client.put("/auth/users/user-2", json={"rsi_handle": "NewHandle"})

        assert response.status_code == 200
        data = response.json()
        assert data["rsi_handle"] == "NewHandle"
        assert data["rsi_verified"] is False
        mock_auth_service.update_user.assert_called_once_with("user-2", {"rsi_handle": "NewHandle"})


class TestUpdateUserUnauthorized:
    def test_non_admin_edit_another_user_returns_403(
        self, regular_client: TestClient, mock_auth_service: MagicMock
    ) -> None:
        response = regular_client.put("/auth/users/user-2", json={"username": "hijack"})

        assert response.status_code == 403
        mock_auth_service.update_user.assert_not_called()


class TestUpdateUserValidation:
    def test_invalid_rsi_handle_format_returns_422(self, client: TestClient) -> None:
        response = client.put("/auth/users/user-1", json={"rsi_handle": "ab"})

        assert response.status_code == 422

    def test_rsi_handle_special_chars_returns_422(self, client: TestClient) -> None:
        response = client.put("/auth/users/user-1", json={"rsi_handle": "bad handle!"})

        assert response.status_code == 422


class TestUpdateUserConflict:
    def test_duplicate_username_returns_409_with_field(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.update_user.side_effect = UserAlreadyExistsError("taken", field="username")

        response = client.put("/auth/users/user-1", json={"username": "taken"})

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["field"] == "username"
        assert data["detail"]["message"] == "Username already taken"

    def test_duplicate_rsi_handle_returns_409_with_field(
        self, client: TestClient, mock_auth_service: MagicMock
    ) -> None:
        mock_auth_service.update_user.side_effect = UserAlreadyExistsError("TakenHandle", field="rsi_handle")

        response = client.put("/auth/users/user-1", json={"rsi_handle": "TakenHandle"})

        assert response.status_code == 409
        data = response.json()
        assert data["detail"]["field"] == "rsi_handle"
        assert data["detail"]["message"] == "RSI handle already registered"


class TestUpdateUserValueError:
    def test_disallowed_field_returns_400(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.update_user.side_effect = ValueError("Field not editable: hashed_password")

        response = client.put("/auth/users/user-1", json={"username": "newname"})

        assert response.status_code == 400


class TestUpdateUserNotFound:
    def test_user_not_found_returns_404(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.update_user.side_effect = UserNotFoundError("missing")

        response = client.put("/auth/users/missing", json={"username": "newname"})

        assert response.status_code == 404
