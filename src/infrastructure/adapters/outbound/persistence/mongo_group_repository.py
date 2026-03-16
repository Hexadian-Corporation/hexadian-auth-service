from bson import ObjectId
from pymongo.collection import Collection

from src.application.ports.outbound.group_repository import GroupRepository
from src.domain.models.group import Group
from src.infrastructure.adapters.outbound.persistence.group_persistence_mapper import GroupPersistenceMapper


class MongoGroupRepository(GroupRepository):
    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def save(self, group: Group) -> Group:
        doc = GroupPersistenceMapper.to_document(group)
        if group.id:
            self._collection.replace_one({"_id": ObjectId(group.id)}, doc, upsert=True)
            return group
        result = self._collection.insert_one(doc)
        group.id = str(result.inserted_id)
        return group

    def find_by_id(self, group_id: str) -> Group | None:
        doc = self._collection.find_one({"_id": ObjectId(group_id)})
        if doc is None:
            return None
        return GroupPersistenceMapper.to_domain(doc)

    def find_by_name(self, name: str) -> Group | None:
        doc = self._collection.find_one({"name": name})
        if doc is None:
            return None
        return GroupPersistenceMapper.to_domain(doc)

    def find_all(self) -> list[Group]:
        return [GroupPersistenceMapper.to_domain(doc) for doc in self._collection.find()]

    def find_by_ids(self, group_ids: list[str]) -> list[Group]:
        object_ids = [ObjectId(gid) for gid in group_ids]
        return [GroupPersistenceMapper.to_domain(doc) for doc in self._collection.find({"_id": {"$in": object_ids}})]

    def delete(self, group_id: str) -> bool:
        result = self._collection.delete_one({"_id": ObjectId(group_id)})
        return result.deleted_count > 0
