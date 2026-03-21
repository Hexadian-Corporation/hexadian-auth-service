from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from src.application.ports.outbound.role_repository import RoleRepository
from src.domain.models.role import Role
from src.infrastructure.adapters.outbound.persistence.role_persistence_mapper import RolePersistenceMapper


class MongoRoleRepository(RoleRepository):
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def save(self, role: Role) -> Role:
        doc = RolePersistenceMapper.to_document(role)
        if role.id:
            await self._collection.replace_one({"_id": ObjectId(role.id)}, doc, upsert=True)
            return role
        result = await self._collection.insert_one(doc)
        role.id = str(result.inserted_id)
        return role

    async def find_by_id(self, role_id: str) -> Role | None:
        doc = await self._collection.find_one({"_id": ObjectId(role_id)})
        if doc is None:
            return None
        return RolePersistenceMapper.to_domain(doc)

    async def find_by_name(self, name: str) -> Role | None:
        doc = await self._collection.find_one({"name": name})
        if doc is None:
            return None
        return RolePersistenceMapper.to_domain(doc)

    async def find_all(self) -> list[Role]:
        docs = await self._collection.find().to_list(length=None)
        return [RolePersistenceMapper.to_domain(doc) for doc in docs]

    async def find_by_ids(self, role_ids: list[str]) -> list[Role]:
        object_ids = [ObjectId(rid) for rid in role_ids]
        docs = await self._collection.find({"_id": {"$in": object_ids}}).to_list(length=None)
        return [RolePersistenceMapper.to_domain(doc) for doc in docs]

    async def delete(self, role_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(role_id)})
        return result.deleted_count > 0
