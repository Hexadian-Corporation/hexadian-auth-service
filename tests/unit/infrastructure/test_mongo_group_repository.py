from unittest.mock import MagicMock

import pytest

from src.domain.models.group import Group
from src.infrastructure.adapters.outbound.persistence.mongo_group_repository import MongoGroupRepository


@pytest.fixture()
def mock_collection() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def repository(mock_collection: MagicMock) -> MongoGroupRepository:
    return MongoGroupRepository(collection=mock_collection)


class TestGroupSave:
    def test_insert_new_group_sets_id(self, repository: MongoGroupRepository, mock_collection: MagicMock) -> None:
        group = Group(name="Admins", description="Admin group", role_ids=["r1"])
        mock_collection.insert_one.return_value = MagicMock(inserted_id="generated_id")

        result = repository.save(group)

        assert result.id == "generated_id"
        mock_collection.insert_one.assert_called_once()

    def test_replace_existing_group(self, repository: MongoGroupRepository, mock_collection: MagicMock) -> None:
        group = Group(id="507f1f77bcf86cd799439011", name="Admins", description="Admin group")

        result = repository.save(group)

        assert result is group
        mock_collection.replace_one.assert_called_once()


class TestGroupFind:
    def test_find_by_id_returns_group(self, repository: MongoGroupRepository, mock_collection: MagicMock) -> None:
        mock_collection.find_one.return_value = {
            "_id": "507f1f77bcf86cd799439011",
            "name": "Admins",
            "description": "Admin group",
            "role_ids": ["r1"],
        }

        result = repository.find_by_id("507f1f77bcf86cd799439011")

        assert result is not None
        assert result.name == "Admins"

    def test_find_by_id_returns_none(self, repository: MongoGroupRepository, mock_collection: MagicMock) -> None:
        mock_collection.find_one.return_value = None

        result = repository.find_by_id("507f1f77bcf86cd799439012")

        assert result is None

    def test_find_by_name_returns_group(self, repository: MongoGroupRepository, mock_collection: MagicMock) -> None:
        mock_collection.find_one.return_value = {
            "_id": "abc123",
            "name": "Admins",
            "description": "Admin group",
            "role_ids": [],
        }

        result = repository.find_by_name("Admins")

        assert result is not None
        assert result.name == "Admins"

    def test_find_by_name_returns_none(self, repository: MongoGroupRepository, mock_collection: MagicMock) -> None:
        mock_collection.find_one.return_value = None

        result = repository.find_by_name("nonexistent")

        assert result is None

    def test_find_all(self, repository: MongoGroupRepository, mock_collection: MagicMock) -> None:
        mock_collection.find.return_value = [
            {"_id": "1", "name": "Admins", "description": "Admin group", "role_ids": []},
            {"_id": "2", "name": "Users", "description": "Regular users", "role_ids": []},
        ]

        result = repository.find_all()

        assert len(result) == 2

    def test_find_by_ids(self, repository: MongoGroupRepository, mock_collection: MagicMock) -> None:
        mock_collection.find.return_value = [
            {"_id": "1", "name": "Admins", "description": "Admin group", "role_ids": []},
        ]

        result = repository.find_by_ids(["507f1f77bcf86cd799439011"])

        assert len(result) == 1
        mock_collection.find.assert_called_once()

    def test_find_by_app_id_returns_matching_groups(
        self, repository: MongoGroupRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.find.return_value = [
            {
                "_id": "1",
                "name": "Users",
                "description": "Users group",
                "role_ids": [],
                "auto_assign_apps": ["hhh-frontend"],
            },
        ]

        result = repository.find_by_app_id("hhh-frontend")

        assert len(result) == 1
        assert result[0].name == "Users"
        assert result[0].auto_assign_apps == ["hhh-frontend"]
        mock_collection.find.assert_called_once_with({"auto_assign_apps": "hhh-frontend"})

    def test_find_by_app_id_returns_empty_when_no_match(
        self, repository: MongoGroupRepository, mock_collection: MagicMock
    ) -> None:
        mock_collection.find.return_value = []

        result = repository.find_by_app_id("unknown-app")

        assert result == []


class TestGroupDelete:
    def test_delete_returns_true(self, repository: MongoGroupRepository, mock_collection: MagicMock) -> None:
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

        assert repository.delete("507f1f77bcf86cd799439011") is True

    def test_delete_returns_false(self, repository: MongoGroupRepository, mock_collection: MagicMock) -> None:
        mock_collection.delete_one.return_value = MagicMock(deleted_count=0)

        assert repository.delete("507f1f77bcf86cd799439011") is False
