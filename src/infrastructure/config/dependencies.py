from opyoid import Module, SingletonScope
from pymongo import MongoClient
from pymongo.collection import Collection

from src.application.ports.inbound.auth_service import AuthService
from src.application.ports.outbound.auth_code_repository import AuthCodeRepository
from src.application.ports.outbound.refresh_token_repository import RefreshTokenRepository
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.auth_service_impl import AuthServiceImpl
from src.infrastructure.adapters.outbound.http.rsi_profile_fetcher_impl import RsiProfileFetcherImpl
from src.infrastructure.adapters.outbound.persistence.mongo_auth_code_repository import MongoAuthCodeRepository
from src.infrastructure.adapters.outbound.persistence.mongo_refresh_token_repository import (
    MongoRefreshTokenRepository,
)
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

        refresh_tokens_collection = db["refresh_tokens"]
        refresh_tokens_collection.create_index("token", unique=True)
        refresh_tokens_collection.create_index("expires_at", expireAfterSeconds=0)

        auth_codes_collection = db["auth_codes"]
        auth_codes_collection.create_index("code", unique=True)
        auth_codes_collection.create_index("expires_at", expireAfterSeconds=0)

        self.bind(Settings, to_instance=self._settings, scope=SingletonScope)
        self.bind(Collection, to_instance=users_collection, scope=SingletonScope)
        self.bind(UserRepository, to_class=MongoUserRepository, scope=SingletonScope)
        self.bind(RsiProfileFetcher, to_class=RsiProfileFetcherImpl, scope=SingletonScope)
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
