from unittest.mock import MagicMock

import pytest

from src.domain.models.role import Role
from src.infrastructure.adapters.outbound.persistence.mongo_role_repository import MongoRoleRepository


@pytest.fixture()
def mock_collection() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def repository(mock_collection: MagicMock) -> MongoRoleRepository:
    return MongoRoleRepository(collection=mock_collection)


class TestRoleSave:
    def test_insert_new_role_sets_id(self, repository: MongoRoleRepository, mock_collection: MagicMock) -> None:
        role = Role(name="Content Manager", description="Manages content", permission_ids=["p1"])
        mock_collection.insert_one.return_value = MagicMock(inserted_id="generated_id")

        result = repository.save(role)

        assert result.id == "generated_id"
        mock_collection.insert_one.assert_called_once()

    def test_replace_existing_role(self, repository: MongoRoleRepository, mock_collection: MagicMock) -> None:
        role = Role(id="507f1f77bcf86cd799439011", name="Content Manager", description="Manages content")

        result = repository.save(role)

        assert result is role
        mock_collection.replace_one.assert_called_once()


class TestRoleFind:
    def test_find_by_id_returns_role(self, repository: MongoRoleRepository, mock_collection: MagicMock) -> None:
        mock_collection.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "Content Manager",
            "description": "Manages content",
            "permission_ids": ["p1"],
        }

        result = repository.find_by_id("507f1f77bcf86cd799439011")

        assert result is not None
        assert result.name == "Content Manager"

    def test_find_by_id_returns_none(self, repository: MongoRoleRepository, mock_collection: MagicMock) -> None:
        mock_collection.find_one.return_value = None

        result = repository.find_by_id("507f1f77bcf86cd799439012")

        assert result is None

    def test_find_by_name_returns_role(self, repository: MongoRoleRepository, mock_collection: MagicMock) -> None:
        mock_collection.find_one.return_value = {
            "_id": "abc123",
            "name": "Content Manager",
            "description": "Manages content",
            "permission_ids": [],
        }

        result = repository.find_by_name("Content Manager")

        assert result is not None
        assert result.name == "Content Manager"

    def test_find_by_name_returns_none(self, repository: MongoRoleRepository, mock_collection: MagicMock) -> None:
        mock_collection.find_one.return_value = None

        result = repository.find_by_name("nonexistent")

        assert result is None

    def test_find_all(self, repository: MongoRoleRepository, mock_collection: MagicMock) -> None:
        mock_collection.find.return_value = [
            {"_id": "1", "name": "Admin", "description": "Admin role", "permission_ids": []},
            {"_id": "2", "name": "Editor", "description": "Editor role", "permission_ids": []},
        ]

        result = repository.find_all()

        assert len(result) == 2

    def test_find_by_ids(self, repository: MongoRoleRepository, mock_collection: MagicMock) -> None:
        mock_collection.find.return_value = [
            {"_id": "1", "name": "Admin", "description": "Admin role", "permission_ids": []},
        ]

        result = repository.find_by_ids(["507f1f77bcf86cd799439011"])

        assert len(result) == 1
        mock_collection.find.assert_called_once()


class TestRoleDelete:
    def test_delete_returns_true(self, repository: MongoRoleRepository, mock_collection: MagicMock) -> None:
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

        assert repository.delete("507f1f77bcf86cd799439011") is True

    def test_delete_returns_false(self, repository: MongoRoleRepository, mock_collection: MagicMock) -> None:
        mock_collection.delete_one.return_value = MagicMock(deleted_count=0)

        assert repository.delete("507f1f77bcf86cd799439011") is False
