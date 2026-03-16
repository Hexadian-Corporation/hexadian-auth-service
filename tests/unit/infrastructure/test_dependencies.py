from unittest.mock import MagicMock, patch

from src.infrastructure.config.dependencies import AppModule
from src.infrastructure.config.settings import Settings


class TestAppModuleIndexes:
    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_username_index(self, mock_mongo_client: MagicMock) -> None:
        mock_collections: dict[str, MagicMock] = {}
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(side_effect=lambda name: mock_collections.setdefault(name, MagicMock()))
        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_mongo_client.return_value = mock_client_instance

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        mock_collections["users"].create_index.assert_any_call("username", unique=True)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_rsi_handle_index(self, mock_mongo_client: MagicMock) -> None:
        mock_collections: dict[str, MagicMock] = {}
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(side_effect=lambda name: mock_collections.setdefault(name, MagicMock()))
        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_mongo_client.return_value = mock_client_instance

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        mock_collections["users"].create_index.assert_any_call("rsi_handle", unique=True)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_permission_code_index(self, mock_mongo_client: MagicMock) -> None:
        mock_collections: dict[str, MagicMock] = {}
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(side_effect=lambda name: mock_collections.setdefault(name, MagicMock()))
        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_mongo_client.return_value = mock_client_instance

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        mock_collections["permissions"].create_index.assert_any_call("code", unique=True)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_role_name_index(self, mock_mongo_client: MagicMock) -> None:
        mock_collections: dict[str, MagicMock] = {}
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(side_effect=lambda name: mock_collections.setdefault(name, MagicMock()))
        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_mongo_client.return_value = mock_client_instance

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        mock_collections["roles"].create_index.assert_any_call("name", unique=True)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_group_name_index(self, mock_mongo_client: MagicMock) -> None:
        mock_collections: dict[str, MagicMock] = {}
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(side_effect=lambda name: mock_collections.setdefault(name, MagicMock()))
        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_mongo_client.return_value = mock_client_instance

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        mock_collections["groups"].create_index.assert_any_call("name", unique=True)
