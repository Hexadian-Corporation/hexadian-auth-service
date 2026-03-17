from unittest.mock import MagicMock

import pytest

from src.domain.models.permission import Permission
from src.infrastructure.adapters.outbound.persistence.mongo_permission_repository import MongoPermissionRepository


@pytest.fixture()
def mock_collection() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def repository(mock_collection: MagicMock) -> MongoPermissionRepository:
    return MongoPermissionRepository(collection=mock_collection)


class TestPermissionSave:
    def test_insert_new_permission_sets_id(
        self, repository: MongoPermissionRepository, mock_collection: MagicMock
    ) -> None:
        permission = Permission(code="hhh:contracts:read", description="View contracts")
        mock_collection.insert_one.return_value = MagicMock(inserted_id="generated_id")

        result = repository.save(permission)

        assert result.id == "generated_id"
        mock_collection.insert_one.assert_called_once()

    def test_replace_existing_permission(
        self, repository: MongoPermissionRepository, mock_collection: MagicMock
    ) -> None:
        permission = Permission(id="507f1f77bcf86cd799439011", code="hhh:contracts:read", description="View contracts")

        result = repository.save(permission)

        assert result is permission
        mock_collection.replace_one.assert_called_once()


class TestPermissionFind:
    def test_find_by_id_returns_permission(
        self, repository: MongoPermissionRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "code": "hhh:contracts:read",
            "description": "View contracts",
        }

        result = repository.find_by_id("507f1f77bcf86cd799439011")

        assert result is not None
        assert result.code == "hhh:contracts:read"

    def test_find_by_id_returns_none(self, repository: MongoPermissionRepository, mock_collection: MagicMock) -> None:
        mock_collection.find_one.return_value = None

        result = repository.find_by_id("507f1f77bcf86cd799439012")

        assert result is None

    def test_find_by_code_returns_permission(
        self, repository: MongoPermissionRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.find_one.return_value = {
            "_id": "abc123",
            "code": "hhh:contracts:read",
            "description": "View contracts",
        }

        result = repository.find_by_code("hhh:contracts:read")

        assert result is not None
        assert result.code == "hhh:contracts:read"

    def test_find_by_code_returns_none(self, repository: MongoPermissionRepository, mock_collection: MagicMock) -> None:
        mock_collection.find_one.return_value = None

        result = repository.find_by_code("nonexistent")

        assert result is None

    def test_find_all(self, repository: MongoPermissionRepository, mock_collection: MagicMock) -> None:
        mock_collection.find.return_value = [
            {"_id": "1", "code": "hhh:contracts:read", "description": "View contracts"},
            {"_id": "2", "code": "hhh:contracts:write", "description": "Edit contracts"},
        ]

        result = repository.find_all()

        assert len(result) == 2

    def test_find_by_ids(self, repository: MongoPermissionRepository, mock_collection: MagicMock) -> None:
        mock_collection.find.return_value = [
            {"_id": "1", "code": "hhh:contracts:read", "description": "View contracts"},
        ]

        result = repository.find_by_ids(["507f1f77bcf86cd799439011"])

        assert len(result) == 1
        mock_collection.find.assert_called_once()


class TestPermissionDelete:
    def test_delete_returns_true(self, repository: MongoPermissionRepository, mock_collection: MagicMock) -> None:
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

        assert repository.delete("507f1f77bcf86cd799439011") is True

    def test_delete_returns_false(self, repository: MongoPermissionRepository, mock_collection: MagicMock) -> None:
        mock_collection.delete_one.return_value = MagicMock(deleted_count=0)

        assert repository.delete("507f1f77bcf86cd799439011") is False
