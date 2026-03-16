from datetime import UTC, datetime
from unittest.mock import MagicMock

from bson import ObjectId

from src.domain.models.auth_code import AuthCode
from src.infrastructure.adapters.outbound.persistence.mongo_auth_code_repository import MongoAuthCodeRepository


class TestMongoAuthCodeRepositorySave:
    def test_save_inserts_and_sets_id(self) -> None:
        collection = MagicMock()
        inserted_id = ObjectId()
        collection.insert_one.return_value = MagicMock(inserted_id=inserted_id)

        repo = MongoAuthCodeRepository(collection)
        auth_code = AuthCode(code="test-code", user_id="user-1")

        result = repo.save(auth_code)

        collection.insert_one.assert_called_once()
        assert result.id == str(inserted_id)


class TestMongoAuthCodeRepositoryFindByCode:
    def test_find_by_code_returns_auth_code(self) -> None:
        collection = MagicMock()
        doc = {
            "_id": ObjectId(),
            "code": "test-code",
            "user_id": "user-1",
            "redirect_uri": "http://localhost:3000/callback",
            "state": "state123",
            "expires_at": datetime(2026, 1, 1, tzinfo=UTC),
            "used": False,
        }
        collection.find_one.return_value = doc

        repo = MongoAuthCodeRepository(collection)
        result = repo.find_by_code("test-code")

        collection.find_one.assert_called_once_with({"code": "test-code"})
        assert result is not None
        assert result.code == "test-code"
        assert result.user_id == "user-1"

    def test_find_by_code_returns_none_when_not_found(self) -> None:
        collection = MagicMock()
        collection.find_one.return_value = None

        repo = MongoAuthCodeRepository(collection)
        result = repo.find_by_code("nonexistent")

        assert result is None


class TestMongoAuthCodeRepositoryMarkUsed:
    def test_mark_used_updates_document(self) -> None:
        collection = MagicMock()

        repo = MongoAuthCodeRepository(collection)
        repo.mark_used("test-code")

        collection.update_one.assert_called_once_with({"code": "test-code"}, {"$set": {"used": True}})
