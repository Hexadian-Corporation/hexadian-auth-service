from opyoid import Module, SingletonScope
from pymongo import MongoClient
from pymongo.collection import Collection

from src.application.ports.inbound.auth_service import AuthService
from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.permission_repository import PermissionRepository
from src.application.ports.outbound.role_repository import RoleRepository
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.auth_service_impl import AuthServiceImpl
from src.infrastructure.adapters.outbound.http.rsi_profile_fetcher_impl import RsiProfileFetcherImpl
from src.infrastructure.adapters.outbound.persistence.mongo_group_repository import MongoGroupRepository
from src.infrastructure.adapters.outbound.persistence.mongo_permission_repository import MongoPermissionRepository
from src.infrastructure.adapters.outbound.persistence.mongo_role_repository import MongoRoleRepository
from src.infrastructure.adapters.outbound.persistence.mongo_user_repository import MongoUserRepository
from src.infrastructure.config.settings import Settings


class AppModule(Module):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings

    def configure(self) -> None:
        client = MongoClient(self._settings.mongo_uri)
        db = client[self._settings.mongo_db]

        users_collection = db["users"]
        users_collection.create_index("username", unique=True)
        users_collection.create_index("rsi_handle", unique=True)

        permissions_collection = db["permissions"]
        permissions_collection.create_index("code", unique=True)

        roles_collection = db["roles"]
        roles_collection.create_index("name", unique=True)

        groups_collection = db["groups"]
        groups_collection.create_index("name", unique=True)

        self.bind(Collection, to_instance=users_collection, named="users", scope=SingletonScope)
        self.bind(Collection, to_instance=permissions_collection, named="permissions", scope=SingletonScope)
        self.bind(Collection, to_instance=roles_collection, named="roles", scope=SingletonScope)
        self.bind(Collection, to_instance=groups_collection, named="groups", scope=SingletonScope)

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
        self.bind(RsiProfileFetcher, to_class=RsiProfileFetcherImpl, scope=SingletonScope)
        self.bind(AuthService, to_class=AuthServiceImpl, scope=SingletonScope)
