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
        user = User(username="newuser", email="new@example.com", hashed_password="hash")
        mock_collection.insert_one.return_value = MagicMock(inserted_id="generated_id")

        result = repository.save(user)

        assert result.id == "generated_id"
        mock_collection.insert_one.assert_called_once()

    def test_replace_existing_user_returns_user(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(id="507f1f77bcf86cd799439011", username="existing", email="e@example.com", hashed_password="hash")

        result = repository.save(user)

        assert result is user
        mock_collection.replace_one.assert_called_once()


class TestSaveDuplicateKeyHandling:
    def test_insert_duplicate_username_raises_user_already_exists(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(username="duplicate", email="a@example.com", hashed_password="hash")
        mock_collection.insert_one.side_effect = DuplicateKeyError("username_1 dup key")

        with pytest.raises(UserAlreadyExistsError):
            repository.save(user)

    def test_insert_duplicate_email_raises_user_already_exists(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(username="user1", email="dup@example.com", hashed_password="hash")
        mock_collection.insert_one.side_effect = DuplicateKeyError("email_1 dup key")

        with pytest.raises(UserAlreadyExistsError):
            repository.save(user)

    def test_replace_duplicate_raises_user_already_exists(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(id="507f1f77bcf86cd799439011", username="existing", email="b@example.com", hashed_password="hash")
        mock_collection.replace_one.side_effect = DuplicateKeyError("username_1 dup key")

        with pytest.raises(UserAlreadyExistsError):
            repository.save(user)

    def test_duplicate_key_error_chains_original_exception(
        self, repository: MongoUserRepository, mock_collection: MagicMock
    ) -> None:
        user = User(username="dup", email="dup@example.com", hashed_password="hash")
        original = DuplicateKeyError("dup key")
        mock_collection.insert_one.side_effect = original

        with pytest.raises(UserAlreadyExistsError) as exc_info:
            repository.save(user)

        assert exc_info.value.__cause__ is original
