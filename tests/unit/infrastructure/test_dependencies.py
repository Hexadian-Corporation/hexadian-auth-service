from unittest.mock import MagicMock, patch

import httpx
import pytest
from opyoid import Injector

from src.application.ports.inbound.auth_service import AuthService
from src.application.ports.inbound.portal_settings_service import PortalSettingsService
from src.application.ports.inbound.rbac_service import RbacService
from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.permission_repository import PermissionRepository
from src.application.ports.outbound.role_repository import RoleRepository
from src.application.ports.outbound.user_repository import UserRepository
from src.infrastructure.config.dependencies import AppModule
from src.infrastructure.config.settings import Settings


@pytest.fixture()
def settings() -> Settings:
    return Settings(jwt_secret="test-secret")


@pytest.fixture()
def http_client() -> httpx.AsyncClient:
    return MagicMock(spec=httpx.AsyncClient)


class TestAppModuleBindings:
    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_configure_binds_auth_service(
        self, mock_motor_cls: MagicMock, settings: Settings, http_client: MagicMock
    ) -> None:
        module = AppModule(settings, http_client)
        injector = Injector([module])

        service = injector.inject(AuthService)

        assert service is not None

    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_configure_binds_rbac_service(
        self, mock_motor_cls: MagicMock, settings: Settings, http_client: MagicMock
    ) -> None:
        module = AppModule(settings, http_client)
        injector = Injector([module])

        service = injector.inject(RbacService)

        assert service is not None

    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_configure_binds_portal_settings_service(
        self, mock_motor_cls: MagicMock, settings: Settings, http_client: MagicMock
    ) -> None:
        module = AppModule(settings, http_client)
        injector = Injector([module])

        service = injector.inject(PortalSettingsService)

        assert service is not None

    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_configure_binds_user_repository(
        self, mock_motor_cls: MagicMock, settings: Settings, http_client: MagicMock
    ) -> None:
        module = AppModule(settings, http_client)
        injector = Injector([module])

        repo = injector.inject(UserRepository)

        assert repo is not None

    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_configure_binds_group_repository(
        self, mock_motor_cls: MagicMock, settings: Settings, http_client: MagicMock
    ) -> None:
        module = AppModule(settings, http_client)
        injector = Injector([module])

        repo = injector.inject(GroupRepository)

        assert repo is not None

    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_configure_binds_permission_repository(
        self, mock_motor_cls: MagicMock, settings: Settings, http_client: MagicMock
    ) -> None:
        module = AppModule(settings, http_client)
        injector = Injector([module])

        repo = injector.inject(PermissionRepository)

        assert repo is not None

    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_configure_binds_role_repository(
        self, mock_motor_cls: MagicMock, settings: Settings, http_client: MagicMock
    ) -> None:
        module = AppModule(settings, http_client)
        injector = Injector([module])

        repo = injector.inject(RoleRepository)

        assert repo is not None

    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_motor_client_is_created_with_mongo_uri(
        self, mock_motor_cls: MagicMock, settings: Settings, http_client: MagicMock
    ) -> None:
        module = AppModule(settings, http_client)
        module.configure()

        mock_motor_cls.assert_called_once_with(settings.mongo_uri)

    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_motor_client_stored_on_module(
        self, mock_motor_cls: MagicMock, settings: Settings, http_client: MagicMock
    ) -> None:
        module = AppModule(settings, http_client)
        module.configure()

        assert module.motor_client is mock_motor_cls.return_value
