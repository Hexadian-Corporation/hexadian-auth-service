import httpx
from motor.motor_asyncio import AsyncIOMotorClient
from opyoid import Module, SingletonScope

from src.application.ports.inbound.auth_service import AuthService
from src.application.ports.inbound.portal_settings_service import PortalSettingsService
from src.application.ports.inbound.rbac_service import RbacService
from src.application.ports.outbound.auth_code_repository import AuthCodeRepository
from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.permission_repository import PermissionRepository
from src.application.ports.outbound.portal_settings_repository import PortalSettingsRepository
from src.application.ports.outbound.refresh_token_repository import RefreshTokenRepository
from src.application.ports.outbound.role_repository import RoleRepository
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.auth_service_impl import AuthServiceImpl
from src.application.services.portal_settings_service_impl import PortalSettingsServiceImpl
from src.application.services.rbac_service_impl import RbacServiceImpl
from src.infrastructure.adapters.outbound.http.rsi_profile_fetcher_impl import RsiProfileFetcherImpl
from src.infrastructure.adapters.outbound.persistence.mongo_auth_code_repository import MongoAuthCodeRepository
from src.infrastructure.adapters.outbound.persistence.mongo_group_repository import MongoGroupRepository
from src.infrastructure.adapters.outbound.persistence.mongo_permission_repository import MongoPermissionRepository
from src.infrastructure.adapters.outbound.persistence.mongo_portal_settings_repository import (
    MongoPortalSettingsRepository,
)
from src.infrastructure.adapters.outbound.persistence.mongo_refresh_token_repository import (
    MongoRefreshTokenRepository,
)
from src.infrastructure.adapters.outbound.persistence.mongo_role_repository import MongoRoleRepository
from src.infrastructure.adapters.outbound.persistence.mongo_user_repository import MongoUserRepository
from src.infrastructure.config.settings import Settings


class AppModule(Module):
    def __init__(self, settings: Settings, http_client: httpx.AsyncClient) -> None:
        super().__init__()
        self._settings = settings
        self._http_client = http_client
        self.motor_client: AsyncIOMotorClient | None = None

    def configure(self) -> None:
        self.motor_client = AsyncIOMotorClient(self._settings.mongo_uri)
        db = self.motor_client[self._settings.mongo_db]

        users_collection = db["users"]
        refresh_tokens_collection = db["refresh_tokens"]
        auth_codes_collection = db["auth_codes"]
        permissions_collection = db["permissions"]
        roles_collection = db["roles"]
        groups_collection = db["groups"]
        portal_settings_collection = db["portal_settings"]

        self.bind(Settings, to_instance=self._settings, scope=SingletonScope)
        self.bind(
            UserRepository,
            to_instance=MongoUserRepository(users_collection),
            scope=SingletonScope,
        )
        self.bind(
            PermissionRepository,
            to_instance=MongoPermissionRepository(permissions_collection),
            scope=SingletonScope,
        )
        self.bind(
            RoleRepository,
            to_instance=MongoRoleRepository(roles_collection),
            scope=SingletonScope,
        )
        self.bind(
            GroupRepository,
            to_instance=MongoGroupRepository(groups_collection),
            scope=SingletonScope,
        )
        self.bind(
            PortalSettingsRepository,
            to_instance=MongoPortalSettingsRepository(portal_settings_collection),
            scope=SingletonScope,
        )
        self.bind(
            RsiProfileFetcher,
            to_instance=RsiProfileFetcherImpl(self._http_client),
            scope=SingletonScope,
        )
        self.bind(
            RefreshTokenRepository,
            to_instance=MongoRefreshTokenRepository(refresh_tokens_collection),
            scope=SingletonScope,
        )
        self.bind(
            AuthCodeRepository,
            to_instance=MongoAuthCodeRepository(auth_codes_collection),
            scope=SingletonScope,
        )
        self.bind(AuthService, to_class=AuthServiceImpl, scope=SingletonScope)
        self.bind(RbacService, to_class=RbacServiceImpl, scope=SingletonScope)
        self.bind(PortalSettingsService, to_class=PortalSettingsServiceImpl, scope=SingletonScope)
