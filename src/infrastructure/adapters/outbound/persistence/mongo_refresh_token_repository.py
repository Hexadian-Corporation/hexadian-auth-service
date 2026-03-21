from motor.motor_asyncio import AsyncIOMotorCollection

from src.application.ports.outbound.refresh_token_repository import RefreshTokenRepository
from src.domain.models.refresh_token import RefreshToken
from src.infrastructure.adapters.outbound.persistence.refresh_token_persistence_mapper import (
    RefreshTokenPersistenceMapper,
)


class MongoRefreshTokenRepository(RefreshTokenRepository):
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def save(self, token: RefreshToken) -> RefreshToken:
        doc = RefreshTokenPersistenceMapper.to_document(token)
        result = await self._collection.insert_one(doc)
        token.id = str(result.inserted_id)
        return token

    async def find_by_token(self, token: str) -> RefreshToken | None:
        doc = await self._collection.find_one({"token": token})
        if doc is None:
            return None
        return RefreshTokenPersistenceMapper.to_domain(doc)

    async def revoke(self, token: str) -> None:
        await self._collection.update_one({"token": token}, {"$set": {"revoked": True}})

    async def revoke_all_for_user(self, user_id: str) -> None:
        await self._collection.update_many({"user_id": user_id}, {"$set": {"revoked": True}})
