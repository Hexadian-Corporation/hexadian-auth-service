from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth

from src.application.ports.inbound.portal_settings_service import PortalSettingsService
from src.domain.models.portal_settings import PortalSettings
from src.infrastructure.adapters.inbound.api.settings_router import init_settings_router, settings_router


@pytest.fixture()
def mock_settings_service() -> MagicMock:
    return MagicMock(spec=PortalSettingsService)


@pytest.fixture()
def client(mock_settings_service: MagicMock) -> TestClient:
    init_settings_router(mock_settings_service)
    app = FastAPI()
    app.include_router(settings_router)

    async def _mock_jwt_auth() -> UserContext:
        return UserContext(
            user_id="user-1",
            username="admin",
            permissions=["auth:settings:manage"],
        )

    app.dependency_overrides[_stub_jwt_auth] = _mock_jwt_auth
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /settings/portal (public)
# ---------------------------------------------------------------------------


class TestGetPortalRedirect:
    def test_returns_redirect_url(self, client: TestClient, mock_settings_service: MagicMock) -> None:
        mock_settings_service.get_settings.return_value = PortalSettings(
            id="s-1", default_redirect_url="https://www.hexadian.com"
        )

        response = client.get("/settings/portal")

        assert response.status_code == 200
        data = response.json()
        assert data["default_redirect_url"] == "https://www.hexadian.com"
        assert "_id" not in data

    def test_returns_custom_redirect_url(self, client: TestClient, mock_settings_service: MagicMock) -> None:
        mock_settings_service.get_settings.return_value = PortalSettings(
            id="s-1", default_redirect_url="https://custom.example.com"
        )

        response = client.get("/settings/portal")

        assert response.status_code == 200
        assert response.json()["default_redirect_url"] == "https://custom.example.com"


# ---------------------------------------------------------------------------
# GET /settings (requires auth:settings:manage)
# ---------------------------------------------------------------------------


class TestGetSettings:
    def test_returns_full_settings(self, client: TestClient, mock_settings_service: MagicMock) -> None:
        mock_settings_service.get_settings.return_value = PortalSettings(
            id="s-1", default_redirect_url="https://www.hexadian.com"
        )

        response = client.get("/settings")

        assert response.status_code == 200
        data = response.json()
        assert data["_id"] == "s-1"
        assert data["default_redirect_url"] == "https://www.hexadian.com"

    def test_requires_permission(self, mock_settings_service: MagicMock) -> None:
        init_settings_router(mock_settings_service)
        app = FastAPI()
        app.include_router(settings_router)

        async def _mock_jwt_auth_no_perms() -> UserContext:
            return UserContext(user_id="user-1", username="testuser", permissions=[])

        app.dependency_overrides[_stub_jwt_auth] = _mock_jwt_auth_no_perms
        no_perms_client = TestClient(app)

        response = no_perms_client.get("/settings")

        assert response.status_code == 403


# ---------------------------------------------------------------------------
# PUT /settings (requires auth:settings:manage)
# ---------------------------------------------------------------------------


class TestUpdateSettings:
    def test_updates_and_returns_settings(self, client: TestClient, mock_settings_service: MagicMock) -> None:
        mock_settings_service.update_settings.return_value = PortalSettings(
            id="s-1", default_redirect_url="https://new.example.com"
        )

        response = client.put("/settings", json={"default_redirect_url": "https://new.example.com"})

        assert response.status_code == 200
        data = response.json()
        assert data["_id"] == "s-1"
        assert data["default_redirect_url"] == "https://new.example.com"
        mock_settings_service.update_settings.assert_called_once_with("https://new.example.com")

    def test_requires_permission(self, mock_settings_service: MagicMock) -> None:
        init_settings_router(mock_settings_service)
        app = FastAPI()
        app.include_router(settings_router)

        async def _mock_jwt_auth_no_perms() -> UserContext:
            return UserContext(user_id="user-1", username="testuser", permissions=[])

        app.dependency_overrides[_stub_jwt_auth] = _mock_jwt_auth_no_perms
        no_perms_client = TestClient(app)

        response = no_perms_client.put("/settings", json={"default_redirect_url": "https://x.com"})

        assert response.status_code == 403
