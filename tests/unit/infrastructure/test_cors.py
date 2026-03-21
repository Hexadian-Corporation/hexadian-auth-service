from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from starlette.middleware.cors import CORSMiddleware


def _make_motor_mock() -> MagicMock:
    """Create a motor client mock with async-compatible collections."""
    mock_collection = AsyncMock()
    mock_db = MagicMock()
    mock_db.__getitem__ = MagicMock(return_value=mock_collection)
    mock_motor = MagicMock()
    mock_motor.__getitem__ = MagicMock(return_value=mock_db)
    return mock_motor


def _create_test_app() -> "FastAPI":  # noqa: F821
    """Create a FastAPI app with CORS middleware, bypassing MongoDB."""
    with (
        patch("src.infrastructure.config.dependencies.AsyncIOMotorClient") as mock_cls,
        patch("src.main._admin_exists", new_callable=AsyncMock) as mock_admin,
        patch("src.main.seed_rbac") as mock_seed,
    ):
        mock_cls.return_value = _make_motor_mock()
        mock_admin.return_value = True
        mock_seed.seed = AsyncMock()
        from src.main import create_app

        return create_app()


class TestCorsMiddleware:
    def test_cors_middleware_is_registered(self) -> None:
        app = _create_test_app()

        cors_middlewares = [m for m in app.user_middleware if m.cls is CORSMiddleware]
        assert len(cors_middlewares) == 1

    def test_cors_preflight_returns_correct_headers(self) -> None:
        app = _create_test_app()
        with (
            patch("src.main._admin_exists", new_callable=AsyncMock) as mock_admin,
            patch("src.main.seed_rbac") as mock_seed,
        ):
            mock_admin.return_value = True
            mock_seed.seed = AsyncMock()
            client = TestClient(app)

            response = client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert "GET" in response.headers["access-control-allow-methods"]
        assert response.headers["access-control-allow-credentials"] == "true"

    def test_cors_header_on_regular_response(self) -> None:
        app = _create_test_app()
        with (
            patch("src.main._admin_exists", new_callable=AsyncMock) as mock_admin,
            patch("src.main.seed_rbac") as mock_seed,
        ):
            mock_admin.return_value = True
            mock_seed.seed = AsyncMock()
            client = TestClient(app)

            response = client.get("/health", headers={"Origin": "http://localhost:3000"})

        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"

    def test_cors_rejects_unknown_origin(self) -> None:
        app = _create_test_app()
        with (
            patch("src.main._admin_exists", new_callable=AsyncMock) as mock_admin,
            patch("src.main.seed_rbac") as mock_seed,
        ):
            mock_admin.return_value = True
            mock_seed.seed = AsyncMock()
            client = TestClient(app)

            response = client.get("/health", headers={"Origin": "http://evil.example.com"})

        assert "access-control-allow-origin" not in response.headers
