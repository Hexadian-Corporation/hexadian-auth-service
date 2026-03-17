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
        error = DuplicateKeyError("username_1 dup key", details={"keyPattern": {"username": 1}})
        mock_collection.insert_one.side_effect = error

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            repository.save(user)

        assert exc_info.value.field == "username"
        assert exc_info.value.identifier == "duplicate"

    def test_insert_duplicate_rsi_handle_raises_user_already_exists(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(username="user1", hashed_password="hash", rsi_handle="DupHandle")
        error = DuplicateKeyError("rsi_handle_1 dup key", details={"keyPattern": {"rsi_handle": 1}})
        mock_collection.insert_one.side_effect = error

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            repository.save(user)

        assert exc_info.value.field == "rsi_handle"
        assert exc_info.value.identifier == "DupHandle"

    def test_replace_duplicate_raises_user_already_exists(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(id="507f1f77bcf86cd799439011", username="existing", hashed_password="hash", rsi_handle="ExPilot")
        error = DuplicateKeyError("username_1 dup key", details={"keyPattern": {"username": 1}})
        mock_collection.replace_one.side_effect = error

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            repository.save(user)

        assert exc_info.value.field == "username"

    def test_replace_duplicate_rsi_handle_raises_with_correct_field(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(id="507f1f77bcf86cd799439011", username="existing", hashed_password="hash", rsi_handle="ExPilot")
        error = DuplicateKeyError("rsi_handle_1 dup key", details={"keyPattern": {"rsi_handle": 1}})
        mock_collection.replace_one.side_effect = error

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            repository.save(user)

        assert exc_info.value.field == "rsi_handle"
        assert exc_info.value.identifier == "ExPilot"

    def test_duplicate_key_error_chains_original_exception(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(username="dup", hashed_password="hash", rsi_handle="DupPilot")
        original = DuplicateKeyError("dup key")
        mock_collection.insert_one.side_effect = original

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            repository.save(user)

        assert exc_info.value.__cause__ is original

    def test_duplicate_key_defaults_to_username_when_no_details(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(username="dup", hashed_password="hash", rsi_handle="DupPilot")
        error = DuplicateKeyError("dup key")
        mock_collection.insert_one.side_effect = error

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            repository.save(user)

        assert exc_info.value.field == "username"


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
        error = DuplicateKeyError("username_1 dup key", details={"keyPattern": {"username": 1}})
        mock_collection.find_one_and_update.side_effect = error

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            repository.update("507f1f77bcf86cd799439011", {"username": "taken"})

        assert exc_info.value.field == "username"

    def test_update_duplicate_rsi_handle_raises_with_correct_field(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        error = DuplicateKeyError("rsi_handle_1 dup key", details={"keyPattern": {"rsi_handle": 1}})
        mock_collection.find_one_and_update.side_effect = error

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            repository.update("507f1f77bcf86cd799439011", {"rsi_handle": "TakenHandle"})

        assert exc_info.value.field == "rsi_handle"
        assert exc_info.value.identifier == "TakenHandle"


class TestFindByRsiHandle:
    def test_find_by_rsi_handle_returns_user(self, repository: MongoUserRepository, mock_collection: MagicMock) -> None:
        from bson import ObjectId

        doc = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "username": "pilot",
            "hashed_password": "hash",
            "group_ids": [],
            "is_active": True,
            "rsi_handle": "TestPilot",
            "rsi_verified": True,
            "rsi_verification_code": None,
        }
        mock_collection.find_one.return_value = doc

        result = repository.find_by_rsi_handle("TestPilot")

        assert result is not None
        assert result.rsi_handle == "TestPilot"
        mock_collection.find_one.assert_called_once_with({"rsi_handle": "TestPilot"})

    def test_find_by_rsi_handle_returns_none_when_not_found(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.find_one.return_value = None

        result = repository.find_by_rsi_handle("NonExistent")

        assert result is None
