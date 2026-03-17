from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth

from src.application.ports.inbound.auth_service import AuthService
from src.domain.exceptions.user_exceptions import (
    InvalidPasswordError,
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


@pytest.fixture()
def client_no_admin(mock_auth_service: MagicMock) -> TestClient:
    from fastapi import FastAPI

    init_router(mock_auth_service)
    app = FastAPI()
    app.include_router(router)

    async def _mock_jwt_auth_no_admin() -> UserContext:
        return UserContext(
            user_id="user-1",
            username="testuser",
            permissions=["auth:users:read"],
        )

    app.dependency_overrides[_stub_jwt_auth] = _mock_jwt_auth_no_admin
    return TestClient(app)


class TestChangePasswordEndpoint:
    def test_change_password_success_returns_204(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        response = client.post(
            "/auth/password/change",
            json={"old_password": "old-secret", "new_password": "new-secret-password"},
        )

        assert response.status_code == 204
        mock_auth_service.change_password.assert_called_once_with("user-1", "old-secret", "new-secret-password")

    def test_change_password_wrong_old_password_returns_400(
        self, client: TestClient, mock_auth_service: MagicMock
    ) -> None:
        mock_auth_service.change_password.side_effect = InvalidPasswordError("Old password is incorrect")

        response = client.post(
            "/auth/password/change",
            json={"old_password": "wrong", "new_password": "new-secret-password"},
        )

        assert response.status_code == 400

    def test_change_password_weak_new_password_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/auth/password/change",
            json={"old_password": "old-secret", "new_password": "short"},
        )

        assert response.status_code == 422

    def test_change_password_user_not_found_returns_404(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.change_password.side_effect = UserNotFoundError("user-1")

        response = client.post(
            "/auth/password/change",
            json={"old_password": "old-secret", "new_password": "new-secret-password"},
        )

        assert response.status_code == 404

    def test_change_password_missing_body_returns_422(self, client: TestClient) -> None:
        response = client.post("/auth/password/change", json={})

        assert response.status_code == 422


class TestResetPasswordEndpoint:
    def test_reset_password_success_returns_204(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        response = client.post(
            "/auth/users/user-1/password-reset",
            json={"new_password": "new-admin-password"},
        )

        assert response.status_code == 204
        mock_auth_service.reset_password.assert_called_once_with("user-1", "new-admin-password")

    def test_reset_password_without_admin_returns_403(self, client_no_admin: TestClient) -> None:
        response = client_no_admin.post(
            "/auth/users/user-1/password-reset",
            json={"new_password": "new-admin-password"},
        )

        assert response.status_code == 403

    def test_reset_password_user_not_found_returns_404(self, client: TestClient, mock_auth_service: MagicMock) -> None:
        mock_auth_service.reset_password.side_effect = UserNotFoundError("nonexistent")

        response = client.post(
            "/auth/users/nonexistent/password-reset",
            json={"new_password": "new-admin-password"},
        )

        assert response.status_code == 404

    def test_reset_password_weak_new_password_returns_422(self, client: TestClient) -> None:
        response = client.post(
            "/auth/users/user-1/password-reset",
            json={"new_password": "short"},
        )

        assert response.status_code == 422

    def test_reset_password_invalid_password_returns_400(
        self, client: TestClient, mock_auth_service: MagicMock
    ) -> None:
        mock_auth_service.reset_password.side_effect = InvalidPasswordError(
            "New password must be at least 8 characters"
        )

        response = client.post(
            "/auth/users/user-1/password-reset",
            json={"new_password": "exactlyeight"},
        )

        assert response.status_code == 400

    def test_reset_password_missing_body_returns_422(self, client: TestClient) -> None:
        response = client.post("/auth/users/user-1/password-reset", json={})

        assert response.status_code == 422
