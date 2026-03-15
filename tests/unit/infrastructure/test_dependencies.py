from unittest.mock import MagicMock, patch

from src.infrastructure.config.dependencies import AppModule
from src.infrastructure.config.settings import Settings


class TestAppModuleIndexes:
    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_username_index(self, mock_mongo_client: MagicMock) -> None:
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_mongo_client.return_value = mock_client_instance

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        mock_collection.create_index.assert_any_call("username", unique=True)

    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_configure_creates_unique_email_index(self, mock_mongo_client: MagicMock) -> None:
        mock_collection = MagicMock()
        mock_db = MagicMock()
        mock_db.__getitem__ = MagicMock(return_value=mock_collection)
        mock_client_instance = MagicMock()
        mock_client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_mongo_client.return_value = mock_client_instance

        settings = Settings(jwt_secret="test-secret")
        module = AppModule(settings)
        module.configure()

        mock_collection.create_index.assert_any_call("email", unique=True)
