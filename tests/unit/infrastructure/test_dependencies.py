from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.config.dependencies import AppModule
from src.infrastructure.config.settings import Settings


@pytest.fixture()
def mock_mongo_collections() -> tuple[MagicMock, dict[str, MagicMock]]:
    collections: dict[str, MagicMock] = {}
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(side_effect=lambda name: collections.setdefault(name, MagicMock()))
    mock_client_instance = MagicMock()
    mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
    mock_mongo_client = MagicMock(return_value=mock_client_instance)
    return mock_mongo_client, collections


class TestAppModuleIndexes:
    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_username_index(
        self, mock_mongo_client: MagicMock, mock_mongo_collections: tuple[MagicMock, dict[str, MagicMock]]
    ) -> None:
        mock_client, collections = mock_mongo_collections
        mock_mongo_client.return_value = mock_client.return_value

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        collections["users"].create_index.assert_any_call("username", unique=True)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_rsi_handle_index(
        self, mock_mongo_client: MagicMock, mock_mongo_collections: tuple[MagicMock, dict[str, MagicMock]]
    ) -> None:
        mock_client, collections = mock_mongo_collections
        mock_mongo_client.return_value = mock_client.return_value

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        collections["users"].create_index.assert_any_call("rsi_handle", unique=True)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_token_index(
        self, mock_mongo_client: MagicMock, mock_mongo_collections: tuple[MagicMock, dict[str, MagicMock]]
    ) -> None:
        mock_client, collections = mock_mongo_collections
        mock_mongo_client.return_value = mock_client.return_value

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        collections["refresh_tokens"].create_index.assert_any_call("token", unique=True)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_ttl_index_on_expires_at(
        self, mock_mongo_client: MagicMock, mock_mongo_collections: tuple[MagicMock, dict[str, MagicMock]]
    ) -> None:
        mock_client, collections = mock_mongo_collections
        mock_mongo_client.return_value = mock_client.return_value

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        collections["refresh_tokens"].create_index.assert_any_call("expires_at", expireAfterSeconds=0)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_auth_code_index(
        self, mock_mongo_client: MagicMock, mock_mongo_collections: tuple[MagicMock, dict[str, MagicMock]]
    ) -> None:
        mock_client, collections = mock_mongo_collections
        mock_mongo_client.return_value = mock_client.return_value

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        collections["auth_codes"].create_index.assert_any_call("code", unique=True)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_ttl_index_on_auth_codes(
        self, mock_mongo_client: MagicMock, mock_mongo_collections: tuple[MagicMock, dict[str, MagicMock]]
    ) -> None:
        mock_client, collections = mock_mongo_collections
        mock_mongo_client.return_value = mock_client.return_value

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        collections["auth_codes"].create_index.assert_any_call("expires_at", expireAfterSeconds=0)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_permission_code_index(
        self, mock_mongo_client: MagicMock, mock_mongo_collections: tuple[MagicMock, dict[str, MagicMock]]
    ) -> None:
        mock_client, collections = mock_mongo_collections
        mock_mongo_client.return_value = mock_client.return_value

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        collections["permissions"].create_index.assert_any_call("code", unique=True)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_role_name_index(
        self, mock_mongo_client: MagicMock, mock_mongo_collections: tuple[MagicMock, dict[str, MagicMock]]
    ) -> None:
        mock_client, collections = mock_mongo_collections
        mock_mongo_client.return_value = mock_client.return_value

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        collections["roles"].create_index.assert_any_call("name", unique=True)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_group_name_index(
        self, mock_mongo_client: MagicMock, mock_mongo_collections: tuple[MagicMock, dict[str, MagicMock]]
    ) -> None:
        mock_client, collections = mock_mongo_collections
        mock_mongo_client.return_value = mock_client.return_value

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        collections["groups"].create_index.assert_any_call("name", unique=True)
