from pymongo.collection import Collection

from src.application.ports.outbound.refresh_token_repository import RefreshTokenRepository
from src.domain.models.refresh_token import RefreshToken
from src.infrastructure.adapters.outbound.persistence.refresh_token_persistence_mapper import (
    RefreshTokenPersistenceMapper,
)


class MongoRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def save(self, token: RefreshToken) -> RefreshToken:
        doc = RefreshTokenPersistenceMapper.to_document(token)
        result = self._collection.insert_one(doc)
        token.id = str(result.inserted_id)
        return token

    def find_by_token(self, token: str) -> RefreshToken | None:
        doc = self._collection.find_one({"token": token})
        if doc is None:
            return None
        return RefreshTokenPersistenceMapper.to_domain(doc)

    def revoke(self, token: str) -> None:
        self._collection.update_one({"token": token}, {"$set": {"revoked": True}})

    def revoke_all_for_user(self, user_id: str) -> None:
        self._collection.update_many({"user_id": user_id}, {"$set": {"revoked": True}})
