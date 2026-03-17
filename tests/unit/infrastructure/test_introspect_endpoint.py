from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth

from src.application.ports.inbound.auth_service import AuthService
from src.domain.models.introspection_result import IntrospectionResult
from src.infrastructure.adapters.inbound.api.auth_router import init_router, router


@pytest.fixture()
def mock_auth_service() -> MagicMock:
    return MagicMock(spec=AuthService)


@pytest.fixture()
def client(mock_auth_service: MagicMock) -> TestClient:
    from fastapi import FastAPI

    init_router(mock_auth_service)
    app = FastAPI()
    app.include_router(router)

    async def _mock_jwt_auth() -> UserContext:
        return UserContext(
            user_id="user-1",
            username="testuser",
            permissions=["users:read", "users:admin"],
        )

    app.dependency_overrides[_stub_jwt_auth] = _mock_jwt_auth
    return TestClient(app)


class TestIntrospectEndpointActiveToken:
    def test_active_token_returns_200_with_full_claims(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
    ) -> None:
        mock_auth_service.introspect_token.return_value = IntrospectionResult(
            active=True,
            sub="user-42",
            username="bob",
            groups=["alpha"],
            roles=["admin"],
            permissions=["contracts:read", "contracts:write"],
            rsi_handle="BobInSpace",
            rsi_verified=True,
            exp=1700000900,
            iat=1700000000,
            is_user_active=True,
        )

        response = client.post("/auth/token/introspect", json={"token": "valid-jwt"})

        assert response.status_code == 200
        data = response.json()
        assert data["active"] is True
        assert data["sub"] == "user-42"
        assert data["username"] == "bob"
        assert data["groups"] == ["alpha"]
        assert data["roles"] == ["admin"]
        assert data["permissions"] == ["contracts:read", "contracts:write"]
        assert data["rsi_handle"] == "BobInSpace"
        assert data["rsi_verified"] is True
        assert data["exp"] == 1700000900
        assert data["iat"] == 1700000000
        assert data["is_user_active"] is True
        assert data["reason"] is None

    def test_introspect_calls_service(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
    ) -> None:
        mock_auth_service.introspect_token.return_value = IntrospectionResult(active=False)

        client.post("/auth/token/introspect", json={"token": "some-token"})

        mock_auth_service.introspect_token.assert_called_once_with("some-token")


class TestIntrospectEndpointInactiveToken:
    def test_invalid_token_returns_200_with_active_false(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
    ) -> None:
        mock_auth_service.introspect_token.return_value = IntrospectionResult(active=False)

        response = client.post("/auth/token/introspect", json={"token": "invalid-jwt"})

        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False
        assert data["sub"] is None
        assert data["username"] is None
        assert data["groups"] is None
        assert data["roles"] is None
        assert data["permissions"] is None
        assert data["reason"] is None

    def test_deactivated_user_returns_200_with_reason(
        self,
        client: TestClient,
        mock_auth_service: MagicMock,
    ) -> None:
        mock_auth_service.introspect_token.return_value = IntrospectionResult(
            active=False,
            sub="user-42",
            reason="user_deactivated",
        )

        response = client.post("/auth/token/introspect", json={"token": "valid-jwt"})

        assert response.status_code == 200
        data = response.json()
        assert data["active"] is False
        assert data["sub"] == "user-42"
        assert data["reason"] == "user_deactivated"


class TestIntrospectEndpointValidation:
    def test_missing_token_field_returns_422(self, client: TestClient) -> None:
        response = client.post("/auth/token/introspect", json={})

        assert response.status_code == 422

    def test_no_auth_required(
        self,
        mock_auth_service: MagicMock,
    ) -> None:
        """Introspect endpoint should work without any JWT auth dependency."""
        from fastapi import FastAPI

        init_router(mock_auth_service)
        app = FastAPI()
        app.include_router(router)
        # No dependency overrides for JWT auth
        no_auth_client = TestClient(app)

        mock_auth_service.introspect_token.return_value = IntrospectionResult(active=False)

        response = no_auth_client.post("/auth/token/introspect", json={"token": "some-token"})

        assert response.status_code == 200
