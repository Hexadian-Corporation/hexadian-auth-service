from bson import ObjectId
from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from src.application.ports.outbound.user_repository import UserRepository
from src.domain.exceptions.user_exceptions import UserAlreadyExistsError
from src.domain.models.user import User
from src.infrastructure.adapters.outbound.persistence.user_persistence_mapper import UserPersistenceMapper


class MongoUserRepository(UserRepository):
    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def save(self, user: User) -> User:
        doc = UserPersistenceMapper.to_document(user)
        try:
            if user.id:
                self._collection.replace_one({"_id": ObjectId(user.id)}, doc, upsert=True)
                return user
            result = self._collection.insert_one(doc)
            user.id = str(result.inserted_id)
            return user
        except DuplicateKeyError as exc:
            key_pattern = exc.details.get("keyPattern", {}) if exc.details else {}
            if "rsi_handle" in key_pattern:
                raise UserAlreadyExistsError(user.rsi_handle, field="rsi_handle") from exc
            raise UserAlreadyExistsError(user.username, field="username") from exc

    def find_by_id(self, user_id: str) -> User | None:
        doc = self._collection.find_one({"_id": ObjectId(user_id)})
        if doc is None:
            return None
        return UserPersistenceMapper.to_domain(doc)

    def find_by_username(self, username: str) -> User | None:
        doc = self._collection.find_one({"username": username})
        if doc is None:
            return None
        return UserPersistenceMapper.to_domain(doc)

    def find_by_rsi_handle(self, rsi_handle: str) -> User | None:
        doc = self._collection.find_one({"rsi_handle": rsi_handle})
        if doc is None:
            return None
        return UserPersistenceMapper.to_domain(doc)

    def find_all(self) -> list[User]:
        return [UserPersistenceMapper.to_domain(doc) for doc in self._collection.find()]

    def delete(self, user_id: str) -> bool:
        result = self._collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

    def update(self, user_id: str, fields: dict) -> User | None:
        try:
            result = self._collection.find_one_and_update(
                {"_id": ObjectId(user_id)},
                {"$set": fields},
                return_document=ReturnDocument.AFTER,
            )
        except DuplicateKeyError as exc:
            key_pattern = exc.details.get("keyPattern", {}) if exc.details else {}
            if "rsi_handle" in key_pattern:
                raise UserAlreadyExistsError(
                    fields.get("rsi_handle", user_id), field="rsi_handle"
                ) from exc
            raise UserAlreadyExistsError(
                fields.get("username", user_id), field="username"
            ) from exc
        if result is None:
            return None
        return UserPersistenceMapper.to_domain(result)
