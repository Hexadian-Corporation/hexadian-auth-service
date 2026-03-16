from pymongo.collection import Collection

from src.application.ports.outbound.auth_code_repository import AuthCodeRepository
from src.domain.models.auth_code import AuthCode
from src.infrastructure.adapters.outbound.persistence.auth_code_persistence_mapper import AuthCodePersistenceMapper


class MongoAuthCodeRepository(AuthCodeRepository):
    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def save(self, auth_code: AuthCode) -> AuthCode:
        doc = AuthCodePersistenceMapper.to_document(auth_code)
        result = self._collection.insert_one(doc)
        auth_code.id = str(result.inserted_id)
        return auth_code

    def find_by_code(self, code: str) -> AuthCode | None:
        doc = self._collection.find_one({"code": code})
        if doc is None:
            return None
        return AuthCodePersistenceMapper.to_domain(doc)

    def mark_used(self, code: str) -> None:
        self._collection.update_one({"code": code}, {"$set": {"used": True}})
