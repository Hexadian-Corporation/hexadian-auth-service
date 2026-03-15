from bson import ObjectId
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
            raise UserAlreadyExistsError(user.username) from exc

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

    def find_by_email(self, email: str) -> User | None:
        doc = self._collection.find_one({"email": email})
        if doc is None:
            return None
        return UserPersistenceMapper.to_domain(doc)

    def find_all(self) -> list[User]:
        return [UserPersistenceMapper.to_domain(doc) for doc in self._collection.find()]

    def delete(self, user_id: str) -> bool:
        result = self._collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
