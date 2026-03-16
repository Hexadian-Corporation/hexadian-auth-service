from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.config.settings import Settings


@pytest.fixture()
def settings() -> Settings:
    return Settings(jwt_secret="test-secret", admin_password="testpass123")


@pytest.fixture()
def mock_collections() -> dict[str, MagicMock]:
    return {
        "groups": MagicMock(),
        "users": MagicMock(),
    }


@pytest.fixture()
def mock_db(mock_collections: dict[str, MagicMock]) -> MagicMock:
    db = MagicMock()
    db.__getitem__ = MagicMock(side_effect=lambda name: mock_collections[name])
    return db


class TestAdminExists:
    @patch("src.main.MongoClient")
    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_returns_false_when_no_admins_group(
        self,
        _mock_deps_mongo: MagicMock,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        from src.main import _admin_exists

        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["groups"].find_one.return_value = None

        assert _admin_exists(settings) is False
        mock_collections["groups"].find_one.assert_called_once_with({"name": "Admins"})
        mock_collections["users"].find_one.assert_not_called()

    @patch("src.main.MongoClient")
    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_returns_false_when_group_exists_but_no_user(
        self,
        _mock_deps_mongo: MagicMock,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        from src.main import _admin_exists

        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["groups"].find_one.return_value = {"_id": "group-123", "name": "Admins"}
        mock_collections["users"].find_one.return_value = None

        assert _admin_exists(settings) is False
        mock_collections["users"].find_one.assert_called_once_with({"group_ids": "group-123"})

    @patch("src.main.MongoClient")
    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_returns_true_when_admin_user_exists(
        self,
        _mock_deps_mongo: MagicMock,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        from src.main import _admin_exists

        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["groups"].find_one.return_value = {"_id": "group-123", "name": "Admins"}
        mock_collections["users"].find_one.return_value = {"_id": "user-1", "username": "admin"}

        assert _admin_exists(settings) is True

    @patch("src.main.MongoClient")
    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_closes_mongo_client(
        self,
        _mock_deps_mongo: MagicMock,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        from src.main import _admin_exists

        client_instance = mock_mongo_client.return_value
        client_instance.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["groups"].find_one.return_value = None

        _admin_exists(settings)

        client_instance.close.assert_called_once()


class TestLifespanSeed:
    @patch("src.main.seed_rbac")
    @patch("src.main._admin_exists", return_value=False)
    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_seeds_when_no_admin(
        self,
        _mock_deps_mongo: MagicMock,
        mock_admin_exists: MagicMock,
        mock_seed_rbac: MagicMock,
    ) -> None:
        from fastapi.testclient import TestClient

        from src.main import create_app

        app = create_app()
        with TestClient(app):
            pass

        mock_seed_rbac.seed.assert_called_once_with(app.state.settings)

    @patch("src.main.seed_rbac")
    @patch("src.main._admin_exists", return_value=True)
    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_skips_seed_when_admin_exists(
        self,
        _mock_deps_mongo: MagicMock,
        mock_admin_exists: MagicMock,
        mock_seed_rbac: MagicMock,
    ) -> None:
        from fastapi.testclient import TestClient

        from src.main import create_app

        app = create_app()
        with TestClient(app):
            pass

        mock_seed_rbac.seed.assert_not_called()

    @patch("src.main.seed_rbac")
    @patch("src.main._admin_exists", return_value=False)
    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_seed_completed_log_message(
        self,
        _mock_deps_mongo: MagicMock,
        _mock_admin_exists: MagicMock,
        _mock_seed_rbac: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        import logging

        from fastapi.testclient import TestClient

        from src.main import create_app

        with caplog.at_level(logging.INFO, logger="src.main"):
            app = create_app()
            with TestClient(app):
                pass

        assert "RBAC seed: completed" in caplog.text

    @patch("src.main.seed_rbac")
    @patch("src.main._admin_exists", return_value=True)
    @patch("src.infrastructure.config.dependencies.MongoClient")
    def test_seed_skipped_log_message(
        self,
        _mock_deps_mongo: MagicMock,
        _mock_admin_exists: MagicMock,
        _mock_seed_rbac: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        import logging

        from fastapi.testclient import TestClient

        from src.main import create_app

        with caplog.at_level(logging.INFO, logger="src.main"):
            app = create_app()
            with TestClient(app):
                pass

        assert "RBAC seed: skipped (admin exists)" in caplog.text
