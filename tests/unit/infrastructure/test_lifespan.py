from unittest.mock import AsyncMock, MagicMock, patch

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
    async def test_returns_false_when_no_admins_group(
        self,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        from src.main import _admin_exists

        mock_collections["groups"].find_one = AsyncMock(return_value=None)
        mock_motor_client = MagicMock()
        mock_motor_client.__getitem__ = MagicMock(return_value=mock_db)

        result = await _admin_exists(mock_motor_client, settings)

        assert result is False
        mock_collections["groups"].find_one.assert_called_once_with({"name": "Admins"})
        mock_collections["users"].find_one.assert_not_called()

    async def test_returns_false_when_group_exists_but_no_user(
        self,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        from src.main import _admin_exists

        mock_collections["groups"].find_one = AsyncMock(return_value={"_id": "group-123", "name": "Admins"})
        mock_collections["users"].find_one = AsyncMock(return_value=None)
        mock_motor_client = MagicMock()
        mock_motor_client.__getitem__ = MagicMock(return_value=mock_db)

        result = await _admin_exists(mock_motor_client, settings)

        assert result is False
        mock_collections["users"].find_one.assert_called_once_with({"group_ids": "group-123"})

    async def test_returns_true_when_admin_user_exists(
        self,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        from src.main import _admin_exists

        mock_collections["groups"].find_one = AsyncMock(return_value={"_id": "group-123", "name": "Admins"})
        mock_collections["users"].find_one = AsyncMock(return_value={"_id": "user-1", "username": "admin"})
        mock_motor_client = MagicMock()
        mock_motor_client.__getitem__ = MagicMock(return_value=mock_db)

        result = await _admin_exists(mock_motor_client, settings)

        assert result is True


def _make_motor_mock() -> MagicMock:
    """Create a motor client mock with async-compatible collections."""
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    mock_motor = MagicMock()
    mock_motor.__getitem__ = MagicMock(return_value=mock_db)
    return mock_motor


class TestLifespanSeed:
    @patch("src.main.seed_rbac")
    @patch("src.main._admin_exists", new_callable=AsyncMock)
    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_seeds_when_no_admin(
        self,
        mock_motor_client_cls: MagicMock,
        mock_admin_exists: AsyncMock,
        mock_seed_rbac: MagicMock,
    ) -> None:
        mock_motor_client_cls.return_value = _make_motor_mock()
        mock_admin_exists.return_value = False
        mock_seed_rbac.seed = AsyncMock()

        from fastapi.testclient import TestClient

        from src.main import create_app

        app = create_app()
        with TestClient(app):
            pass

        mock_seed_rbac.seed.assert_called_once_with(app.state.settings)

    @patch("src.main.seed_rbac")
    @patch("src.main._admin_exists", new_callable=AsyncMock)
    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_skips_seed_when_admin_exists(
        self,
        mock_motor_client_cls: MagicMock,
        mock_admin_exists: AsyncMock,
        mock_seed_rbac: MagicMock,
    ) -> None:
        mock_motor_client_cls.return_value = _make_motor_mock()
        mock_admin_exists.return_value = True
        mock_seed_rbac.seed = AsyncMock()

        from fastapi.testclient import TestClient

        from src.main import create_app

        app = create_app()
        with TestClient(app):
            pass

        mock_seed_rbac.seed.assert_not_called()

    @patch("src.main.seed_rbac")
    @patch("src.main._admin_exists", new_callable=AsyncMock)
    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_seed_completed_log_message(
        self,
        mock_motor_client_cls: MagicMock,
        mock_admin_exists: AsyncMock,
        mock_seed_rbac: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        import logging

        mock_motor_client_cls.return_value = _make_motor_mock()
        mock_admin_exists.return_value = False
        mock_seed_rbac.seed = AsyncMock()

        from fastapi.testclient import TestClient

        from src.main import create_app

        with caplog.at_level(logging.INFO, logger="src.main"):
            app = create_app()
            with TestClient(app):
                pass

        assert "RBAC seed: completed" in caplog.text

    @patch("src.main.seed_rbac")
    @patch("src.main._admin_exists", new_callable=AsyncMock)
    @patch("src.infrastructure.config.dependencies.AsyncIOMotorClient")
    def test_seed_skipped_log_message(
        self,
        mock_motor_client_cls: MagicMock,
        mock_admin_exists: AsyncMock,
        mock_seed_rbac: MagicMock,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        import logging

        mock_motor_client_cls.return_value = _make_motor_mock()
        mock_admin_exists.return_value = True
        mock_seed_rbac.seed = AsyncMock()

        from fastapi.testclient import TestClient

        from src.main import create_app

        with caplog.at_level(logging.INFO, logger="src.main"):
            app = create_app()
            with TestClient(app):
                pass

        assert "RBAC seed: skipped (admin exists)" in caplog.text
