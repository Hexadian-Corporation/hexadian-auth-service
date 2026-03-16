from opyoid import Module, SingletonScope
from pymongo import MongoClient
from pymongo.collection import Collection

from src.application.ports.inbound.auth_service import AuthService
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.auth_service_impl import AuthServiceImpl
from src.infrastructure.adapters.outbound.http.rsi_profile_fetcher_impl import RsiProfileFetcherImpl
from src.infrastructure.adapters.outbound.persistence.mongo_user_repository import MongoUserRepository
from src.infrastructure.config.settings import Settings


class AppModule(Module):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self._settings = settings

    def configure(self) -> None:
        client = MongoClient(self._settings.mongo_uri)
        db = client[self._settings.mongo_db]
        collection = db["users"]
        collection.create_index("username", unique=True)
        collection.create_index("rsi_handle", unique=True)

        self.bind(Collection, to_instance=collection, scope=SingletonScope)
        self.bind(UserRepository, to_class=MongoUserRepository, scope=SingletonScope)
        self.bind(RsiProfileFetcher, to_class=RsiProfileFetcherImpl, scope=SingletonScope)
        self.bind(AuthService, to_class=AuthServiceImpl, scope=SingletonScope)
