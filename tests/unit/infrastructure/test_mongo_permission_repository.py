from unittest.mock import AsyncMock, MagicMock

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
    async def test_insert_new_permission_sets_id(
        self, repository: MongoPermissionRepository, mock_collection: MagicMock
    ) -> None:
        permission = Permission(code="hhh:contracts:read", description="View contracts")
        mock_collection.insert_one = AsyncMock(return_value=MagicMock(inserted_id="generated_id"))

        result = await repository.save(permission)

        assert result.id == "generated_id"
        mock_collection.insert_one.assert_called_once()

    async def test_replace_existing_permission(
        self, repository: MongoPermissionRepository, mock_collection: MagicMock
    ) -> None:
        permission = Permission(id="507f1f77bcf86cd799439011", code="hhh:contracts:read", description="View contracts")
        mock_collection.replace_one = AsyncMock(return_value=MagicMock())

        result = await repository.save(permission)

        assert result is permission
        mock_collection.replace_one.assert_called_once()


class TestPermissionFind:
    async def test_find_by_id_returns_permission(
        self, repository: MongoPermissionRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.find_one = AsyncMock(
            return_value={
                "_id": "507f1f77bcf86cd799439011",
                "code": "hhh:contracts:read",
                "description": "View contracts",
            }
        )

        result = await repository.find_by_id("507f1f77bcf86cd799439011")

        assert result is not None
        assert result.code == "hhh:contracts:read"

    async def test_find_by_id_returns_none(
        self,
        repository: MongoPermissionRepository,
        mock_collection: MagicMock,
    ) -> None:
        mock_collection.find_one = AsyncMock(return_value=None)

        result = await repository.find_by_id("507f1f77bcf86cd799439012")

        assert result is None

    async def test_find_by_code_returns_permission(
        self, repository: MongoPermissionRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.find_one = AsyncMock(
            return_value={
                "_id": "abc123",
                "code": "hhh:contracts:read",
                "description": "View contracts",
            }
        )

        result = await repository.find_by_code("hhh:contracts:read")

        assert result is not None
        assert result.code == "hhh:contracts:read"

    async def test_find_by_code_returns_none(
        self,
        repository: MongoPermissionRepository,
        mock_collection: MagicMock,
    ) -> None:
        mock_collection.find_one = AsyncMock(return_value=None)

        result = await repository.find_by_code("nonexistent")

        assert result is None

    async def test_find_all(self, repository: MongoPermissionRepository, mock_collection: MagicMock) -> None:
        docs = [
            {"_id": "1", "code": "hhh:contracts:read", "description": "View contracts"},
            {"_id": "2", "code": "hhh:contracts:write", "description": "Edit contracts"},
        ]
        mock_collection.find.return_value.to_list = AsyncMock(return_value=docs)

        result = await repository.find_all()

        assert len(result) == 2

    async def test_find_by_ids(self, repository: MongoPermissionRepository, mock_collection: MagicMock) -> None:
        docs = [
            {"_id": "1", "code": "hhh:contracts:read", "description": "View contracts"},
        ]
        mock_collection.find.return_value.to_list = AsyncMock(return_value=docs)

        result = await repository.find_by_ids(["507f1f77bcf86cd799439011"])

        assert len(result) == 1
        mock_collection.find.assert_called_once()


class TestPermissionDelete:
    async def test_delete_returns_true(self, repository: MongoPermissionRepository, mock_collection: MagicMock) -> None:
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1))

        assert await repository.delete("507f1f77bcf86cd799439011") is True

    async def test_delete_returns_false(
        self,
        repository: MongoPermissionRepository,
        mock_collection: MagicMock,
    ) -> None:
        mock_collection.delete_one = AsyncMock(return_value=MagicMock(deleted_count=0))

        assert await repository.delete("507f1f77bcf86cd799439011") is False
