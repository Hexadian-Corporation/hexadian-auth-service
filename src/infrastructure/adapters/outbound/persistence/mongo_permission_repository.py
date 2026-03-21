from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from src.application.ports.outbound.permission_repository import PermissionRepository
from src.domain.models.permission import Permission
from src.infrastructure.adapters.outbound.persistence.permission_persistence_mapper import PermissionPersistenceMapper


class MongoPermissionRepository(PermissionRepository):
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def save(self, permission: Permission) -> Permission:
        doc = PermissionPersistenceMapper.to_document(permission)
        if permission.id:
            await self._collection.replace_one({"_id": ObjectId(permission.id)}, doc, upsert=True)
            return permission
        result = await self._collection.insert_one(doc)
        permission.id = str(result.inserted_id)
        return permission

    async def find_by_id(self, permission_id: str) -> Permission | None:
        doc = await self._collection.find_one({"_id": ObjectId(permission_id)})
        if doc is None:
            return None
        return PermissionPersistenceMapper.to_domain(doc)

    async def find_by_code(self, code: str) -> Permission | None:
        doc = await self._collection.find_one({"code": code})
        if doc is None:
            return None
        return PermissionPersistenceMapper.to_domain(doc)

    async def find_all(self) -> list[Permission]:
        docs = await self._collection.find().to_list(length=None)
        return [PermissionPersistenceMapper.to_domain(doc) for doc in docs]

    async def find_by_ids(self, permission_ids: list[str]) -> list[Permission]:
        object_ids = [ObjectId(pid) for pid in permission_ids]
        docs = await self._collection.find({"_id": {"$in": object_ids}}).to_list(length=None)
        return [PermissionPersistenceMapper.to_domain(doc) for doc in docs]

    async def delete(self, permission_id: str) -> bool:
        result = await self._collection.delete_one({"_id": ObjectId(permission_id)})
        return result.deleted_count > 0
