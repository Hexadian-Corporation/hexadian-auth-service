from datetime import UTC, datetime
from unittest.mock import MagicMock

from bson import ObjectId

from src.domain.models.refresh_token import RefreshToken
from src.infrastructure.adapters.outbound.persistence.mongo_refresh_token_repository import (
    MongoRefreshTokenRepository,
)


class TestMongoRefreshTokenRepositorySave:
    def test_save_inserts_and_sets_id(self) -> None:
        mock_collection = MagicMock()
        mock_collection.insert_one.return_value = MagicMock(inserted_id=ObjectId("507f1f77bcf86cd799439011"))
        repo = MongoRefreshTokenRepository(mock_collection)

        token = RefreshToken(user_id="user-1", token="uuid-token")
        result = repo.save(token)

        assert result.id == "507f1f77bcf86cd799439011"
        mock_collection.insert_one.assert_called_once()


class TestMongoRefreshTokenRepositoryFindByToken:
    def test_find_by_token_returns_token(self) -> None:
        mock_collection = MagicMock()
        expires = datetime(2026, 3, 23, 12, 0, 0, tzinfo=UTC)
        mock_collection.find_one.return_value = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": "user-1",
            "token": "uuid-token",
            "expires_at": expires,
            "revoked": False,
        }
        repo = MongoRefreshTokenRepository(mock_collection)

        result = repo.find_by_token("uuid-token")

        assert result is not None
        assert result.token == "uuid-token"
        assert result.user_id == "user-1"
        mock_collection.find_one.assert_called_once_with({"token": "uuid-token"})

    def test_find_by_token_returns_none_when_not_found(self) -> None:
        mock_collection = MagicMock()
        mock_collection.find_one.return_value = None
        repo = MongoRefreshTokenRepository(mock_collection)

        result = repo.find_by_token("nonexistent")

        assert result is None


class TestMongoRefreshTokenRepositoryRevoke:
    def test_revoke_updates_token(self) -> None:
        mock_collection = MagicMock()
        repo = MongoRefreshTokenRepository(mock_collection)

        repo.revoke("uuid-token")

        mock_collection.update_one.assert_called_once_with(
            {"token": "uuid-token"},
            {"$set": {"revoked": True}},
        )

    def test_revoke_all_for_user(self) -> None:
        mock_collection = MagicMock()
        repo = MongoRefreshTokenRepository(mock_collection)

        repo.revoke_all_for_user("user-1")

        mock_collection.update_many.assert_called_once_with(
            {"user_id": "user-1"},
            {"$set": {"revoked": True}},
        )
