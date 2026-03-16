from unittest.mock import MagicMock

import pytest
from pymongo.errors import DuplicateKeyError

from src.domain.exceptions.user_exceptions import UserAlreadyExistsError
from src.domain.models.user import User
from src.infrastructure.adapters.outbound.persistence.mongo_user_repository import MongoUserRepository


@pytest.fixture()
def mock_collection() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def repository(mock_collection: MagicMock) -> MongoUserRepository:
    return MongoUserRepository(collection=mock_collection)


class TestSaveSuccessPaths:
    def test_insert_new_user_sets_id(self, repository: MongoUserRepository, mock_collection: MagicMock) -> None:
        user = User(username="newuser", hashed_password="hash", rsi_handle="NewPilot")
        mock_collection.insert_one.return_value = MagicMock(inserted_id="generated_id")

        result = repository.save(user)

        assert result.id == "generated_id"
        mock_collection.insert_one.assert_called_once()

    def test_replace_existing_user_returns_user(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(id="507f1f77bcf86cd799439011", username="existing", hashed_password="hash", rsi_handle="ExPilot")

        result = repository.save(user)

        assert result is user
        mock_collection.replace_one.assert_called_once()


class TestSaveDuplicateKeyHandling:
    def test_insert_duplicate_username_raises_user_already_exists(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(username="duplicate", hashed_password="hash", rsi_handle="Pilot1")
        mock_collection.insert_one.side_effect = DuplicateKeyError("username_1 dup key")

        with pytest.raises(UserAlreadyExistsError):
            repository.save(user)

    def test_insert_duplicate_rsi_handle_raises_user_already_exists(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(username="user1", hashed_password="hash", rsi_handle="DupHandle")
        mock_collection.insert_one.side_effect = DuplicateKeyError("rsi_handle_1 dup key")

        with pytest.raises(UserAlreadyExistsError):
            repository.save(user)

    def test_replace_duplicate_raises_user_already_exists(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(id="507f1f77bcf86cd799439011", username="existing", hashed_password="hash", rsi_handle="ExPilot")
        mock_collection.replace_one.side_effect = DuplicateKeyError("username_1 dup key")

        with pytest.raises(UserAlreadyExistsError):
            repository.save(user)

    def test_duplicate_key_error_chains_original_exception(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(username="dup", hashed_password="hash", rsi_handle="DupPilot")
        original = DuplicateKeyError("dup key")
        mock_collection.insert_one.side_effect = original

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            repository.save(user)

        assert exc_info.value.__cause__ is original


class TestUpdateUser:
    def test_update_returns_updated_user(self, repository: MongoUserRepository, mock_collection: MagicMock) -> None:
        from bson import ObjectId

        user_id = "507f1f77bcf86cd799439011"
        updated_doc = {
            "_id": ObjectId(user_id),
            "username": "updated_name",
            "hashed_password": "hash",
            "group_ids": [],
            "is_active": True,
            "rsi_handle": "Pilot",
            "rsi_verified": False,
            "rsi_verification_code": None,
        }
        mock_collection.find_one_and_update.return_value = updated_doc

        result = repository.update(user_id, {"username": "updated_name"})

        assert result is not None
        assert result.username == "updated_name"
        mock_collection.find_one_and_update.assert_called_once()

    def test_update_returns_none_when_user_not_found(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.find_one_and_update.return_value = None

        result = repository.update("507f1f77bcf86cd799439011", {"username": "newname"})

        assert result is None

    def test_update_duplicate_key_raises_user_already_exists(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.find_one_and_update.side_effect = DuplicateKeyError("username_1 dup key")

        with pytest.raises(UserAlreadyExistsError):
            repository.update("507f1f77bcf86cd799439011", {"username": "taken"})
