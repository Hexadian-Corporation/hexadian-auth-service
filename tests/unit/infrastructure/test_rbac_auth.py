from unittest.mock import MagicMock

import jwt
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hexadian_auth_common.fastapi import (
    JWTAuthDependency,
    _stub_jwt_auth,
    register_exception_handlers,
)

from src.application.ports.inbound.rbac_service import RbacService
from src.domain.models.group import Group
from src.domain.models.permission import Permission
from src.domain.models.role import Role
from src.infrastructure.adapters.inbound.api.rbac_router import init_rbac_router, rbac_router

JWT_SECRET = "test-secret-key-for-rbac-auth-tests"
JWT_ALGORITHM = "HS256"


def _make_token(
    sub: str = "user-1",
    username: str = "testuser",
    permissions: list[str] | None = None,
    **extra_claims: object,
) -> str:
    import time

    payload = {
        "sub": sub,
        "username": username,
        "permissions": permissions or [],
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        **extra_claims,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def mock_rbac_service() -> MagicMock:
    return MagicMock(spec=RbacService)


@pytest.fixture()
def client(mock_rbac_service: MagicMock) -> TestClient:
    init_rbac_router(mock_rbac_service)
    app = FastAPI()
    jwt_auth = JWTAuthDependency(secret=JWT_SECRET, algorithm=JWT_ALGORITHM)
    app.dependency_overrides[_stub_jwt_auth] = jwt_auth
    register_exception_handlers(app)
    app.include_router(rbac_router)
    return TestClient(app)


# ---------------------------------------------------------------------------
# No token → 401
# ---------------------------------------------------------------------------


class TestRbacEndpointsNoToken:
    def test_list_permissions_no_token_returns_401(self, client: TestClient) -> None:
        assert client.get("/rbac/permissions").status_code == 401

    def test_create_permission_no_token_returns_401(self, client: TestClient) -> None:
        assert client.post("/rbac/permissions", json={"code": "a", "description": "b"}).status_code == 401

    def test_get_permission_no_token_returns_401(self, client: TestClient) -> None:
        assert client.get("/rbac/permissions/p-1").status_code == 401

    def test_update_permission_no_token_returns_401(self, client: TestClient) -> None:
        assert client.put("/rbac/permissions/p-1", json={"code": "a", "description": "b"}).status_code == 401

    def test_delete_permission_no_token_returns_401(self, client: TestClient) -> None:
        assert client.delete("/rbac/permissions/p-1").status_code == 401

    def test_list_roles_no_token_returns_401(self, client: TestClient) -> None:
        assert client.get("/rbac/roles").status_code == 401

    def test_create_role_no_token_returns_401(self, client: TestClient) -> None:
        assert client.post("/rbac/roles", json={"name": "a", "description": "b"}).status_code == 401

    def test_list_groups_no_token_returns_401(self, client: TestClient) -> None:
        assert client.get("/rbac/groups").status_code == 401

    def test_assign_user_to_group_no_token_returns_401(self, client: TestClient) -> None:
        assert client.post("/rbac/users/u-1/groups", json={"group_id": "g-1"}).status_code == 401

    def test_remove_user_from_group_no_token_returns_401(self, client: TestClient) -> None:
        assert client.delete("/rbac/users/u-1/groups/g-1").status_code == 401

    def test_resolve_permissions_no_token_returns_401(self, client: TestClient) -> None:
        assert client.get("/rbac/users/u-1/permissions").status_code == 401


# ---------------------------------------------------------------------------
# Wrong permissions → 403
# ---------------------------------------------------------------------------


class TestRbacEndpointsWrongPermissions:
    def test_list_permissions_without_rbac_manage_returns_403(self, client: TestClient) -> None:
        token = _make_token(permissions=[])
        assert client.get("/rbac/permissions", headers=_auth_header(token)).status_code == 403

    def test_create_permission_without_rbac_manage_returns_403(self, client: TestClient) -> None:
        token = _make_token(permissions=["users:read"])
        assert (
            client.post("/rbac/permissions", json={"code": "a", "description": "b"}, headers=_auth_header(token))
        ).status_code == 403

    def test_list_roles_without_rbac_manage_returns_403(self, client: TestClient) -> None:
        token = _make_token(permissions=[])
        assert client.get("/rbac/roles", headers=_auth_header(token)).status_code == 403

    def test_list_groups_without_rbac_manage_returns_403(self, client: TestClient) -> None:
        token = _make_token(permissions=[])
        assert client.get("/rbac/groups", headers=_auth_header(token)).status_code == 403

    def test_assign_user_to_group_without_users_admin_returns_403(self, client: TestClient) -> None:
        token = _make_token(permissions=["rbac:manage"])
        assert (
            client.post("/rbac/users/u-1/groups", json={"group_id": "g-1"}, headers=_auth_header(token))
        ).status_code == 403

    def test_remove_user_from_group_without_users_admin_returns_403(self, client: TestClient) -> None:
        token = _make_token(permissions=["rbac:manage"])
        assert client.delete("/rbac/users/u-1/groups/g-1", headers=_auth_header(token)).status_code == 403

    def test_resolve_permissions_other_user_without_users_read_returns_403(self, client: TestClient) -> None:
        token = _make_token(sub="user-1", permissions=[])
        assert client.get("/rbac/users/other-user/permissions", headers=_auth_header(token)).status_code == 403


# ---------------------------------------------------------------------------
# Correct permissions → success
# ---------------------------------------------------------------------------


class TestRbacEndpointsCorrectPermissions:
    def test_list_permissions_with_rbac_manage(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.list_permissions.return_value = []
        token = _make_token(permissions=["rbac:manage"])
        response = client.get("/rbac/permissions", headers=_auth_header(token))
        assert response.status_code == 200

    def test_create_permission_with_rbac_manage(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.create_permission.return_value = Permission(id="p-1", code="a", description="b")
        token = _make_token(permissions=["rbac:manage"])
        response = client.post("/rbac/permissions", json={"code": "a", "description": "b"}, headers=_auth_header(token))
        assert response.status_code == 201

    def test_list_roles_with_rbac_manage(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.list_roles.return_value = []
        token = _make_token(permissions=["rbac:manage"])
        assert client.get("/rbac/roles", headers=_auth_header(token)).status_code == 200

    def test_create_role_with_rbac_manage(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.create_role.return_value = Role(id="r-1", name="a", description="b")
        token = _make_token(permissions=["rbac:manage"])
        response = client.post(
            "/rbac/roles",
            json={"name": "a", "description": "b", "permission_ids": []},
            headers=_auth_header(token),
        )
        assert response.status_code == 201

    def test_list_groups_with_rbac_manage(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.list_groups.return_value = []
        token = _make_token(permissions=["rbac:manage"])
        assert client.get("/rbac/groups", headers=_auth_header(token)).status_code == 200

    def test_create_group_with_rbac_manage(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.create_group.return_value = Group(id="g-1", name="a", description="b")
        token = _make_token(permissions=["rbac:manage"])
        response = client.post(
            "/rbac/groups",
            json={"name": "a", "description": "b", "role_ids": []},
            headers=_auth_header(token),
        )
        assert response.status_code == 201

    def test_assign_user_to_group_with_users_admin(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        token = _make_token(permissions=["users:admin"])
        response = client.post("/rbac/users/u-1/groups", json={"group_id": "g-1"}, headers=_auth_header(token))
        assert response.status_code == 204

    def test_remove_user_from_group_with_users_admin(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        token = _make_token(permissions=["users:admin"])
        response = client.delete("/rbac/users/u-1/groups/g-1", headers=_auth_header(token))
        assert response.status_code == 204

    def test_resolve_permissions_self_access(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.resolve_permissions.return_value = ["users:read"]
        token = _make_token(sub="user-1", permissions=[])
        response = client.get("/rbac/users/user-1/permissions", headers=_auth_header(token))
        assert response.status_code == 200

    def test_resolve_permissions_with_users_read(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.resolve_permissions.return_value = ["users:read"]
        token = _make_token(sub="user-1", permissions=["users:read"])
        response = client.get("/rbac/users/other-user/permissions", headers=_auth_header(token))
        assert response.status_code == 200
