from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth

from src.application.ports.inbound.rbac_service import RbacService
from src.domain.exceptions.group_exceptions import GroupNotFoundError
from src.domain.exceptions.permission_exceptions import PermissionNotFoundError
from src.domain.exceptions.role_exceptions import RoleNotFoundError
from src.domain.exceptions.user_exceptions import UserNotFoundError
from src.domain.models.group import Group
from src.domain.models.permission import Permission
from src.domain.models.role import Role
from src.infrastructure.adapters.inbound.api.rbac_router import init_rbac_router, rbac_router


@pytest.fixture()
def mock_rbac_service() -> MagicMock:
    return MagicMock(spec=RbacService)


@pytest.fixture()
def client(mock_rbac_service: MagicMock) -> TestClient:
    from fastapi import FastAPI

    init_rbac_router(mock_rbac_service)
    app = FastAPI()
    app.include_router(rbac_router)

    async def _mock_jwt_auth() -> UserContext:
        return UserContext(
            user_id="user-1",
            username="admin",
            permissions=["rbac:manage", "users:admin", "users:read"],
        )

    app.dependency_overrides[_stub_jwt_auth] = _mock_jwt_auth
    return TestClient(app)


# ---------------------------------------------------------------------------
# Permission endpoints
# ---------------------------------------------------------------------------


class TestPermissionEndpoints:
    def test_create_permission(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.create_permission.return_value = Permission(
            id="p-1", code="users:read", description="Read users"
        )

        response = client.post("/rbac/permissions", json={"code": "users:read", "description": "Read users"})

        assert response.status_code == 201
        data = response.json()
        assert data["_id"] == "p-1"
        assert data["code"] == "users:read"

    def test_list_permissions(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.list_permissions.return_value = [
            Permission(id="p-1", code="a", description="A"),
            Permission(id="p-2", code="b", description="B"),
        ]

        response = client.get("/rbac/permissions")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_permission(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.get_permission.return_value = Permission(id="p-1", code="users:read", description="Read")

        response = client.get("/rbac/permissions/p-1")

        assert response.status_code == 200
        assert response.json()["_id"] == "p-1"

    def test_get_permission_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.get_permission.side_effect = PermissionNotFoundError("missing")

        response = client.get("/rbac/permissions/missing")

        assert response.status_code == 404

    def test_update_permission(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.update_permission.return_value = Permission(
            id="p-1", code="users:write", description="Write"
        )

        response = client.put("/rbac/permissions/p-1", json={"code": "users:write", "description": "Write"})

        assert response.status_code == 200
        assert response.json()["code"] == "users:write"

    def test_update_permission_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.update_permission.side_effect = PermissionNotFoundError("missing")

        response = client.put("/rbac/permissions/missing", json={"code": "x", "description": "x"})

        assert response.status_code == 404

    def test_delete_permission(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        response = client.delete("/rbac/permissions/p-1")

        assert response.status_code == 204

    def test_delete_permission_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.delete_permission.side_effect = PermissionNotFoundError("missing")

        response = client.delete("/rbac/permissions/missing")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Role endpoints
# ---------------------------------------------------------------------------


class TestRoleEndpoints:
    def test_create_role(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.create_role.return_value = Role(
            id="r-1", name="Admin", description="Admin role", permission_ids=["p-1"]
        )

        response = client.post(
            "/rbac/roles",
            json={"name": "Admin", "description": "Admin role", "permission_ids": ["p-1"]},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["_id"] == "r-1"
        assert data["name"] == "Admin"

    def test_list_roles(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.list_roles.return_value = [Role(id="r-1"), Role(id="r-2")]

        response = client.get("/rbac/roles")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_role(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.get_role.return_value = Role(id="r-1", name="Admin")

        response = client.get("/rbac/roles/r-1")

        assert response.status_code == 200

    def test_get_role_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.get_role.side_effect = RoleNotFoundError("missing")

        response = client.get("/rbac/roles/missing")

        assert response.status_code == 404

    def test_update_role(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.update_role.return_value = Role(id="r-1", name="New", description="New", permission_ids=[])

        response = client.put(
            "/rbac/roles/r-1",
            json={"name": "New", "description": "New", "permission_ids": []},
        )

        assert response.status_code == 200

    def test_update_role_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.update_role.side_effect = RoleNotFoundError("missing")

        response = client.put("/rbac/roles/missing", json={"name": "x", "description": "x", "permission_ids": []})

        assert response.status_code == 404

    def test_delete_role(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        response = client.delete("/rbac/roles/r-1")

        assert response.status_code == 204

    def test_delete_role_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.delete_role.side_effect = RoleNotFoundError("missing")

        response = client.delete("/rbac/roles/missing")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Group endpoints
# ---------------------------------------------------------------------------


class TestGroupEndpoints:
    def test_create_group(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.create_group.return_value = Group(
            id="g-1", name="Admins", description="Admin group", role_ids=["r-1"]
        )

        response = client.post(
            "/rbac/groups",
            json={"name": "Admins", "description": "Admin group", "role_ids": ["r-1"]},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["_id"] == "g-1"

    def test_list_groups(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.list_groups.return_value = [Group(id="g-1"), Group(id="g-2")]

        response = client.get("/rbac/groups")

        assert response.status_code == 200
        assert len(response.json()) == 2

    def test_get_group(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.get_group.return_value = Group(id="g-1", name="Admins")

        response = client.get("/rbac/groups/g-1")

        assert response.status_code == 200

    def test_get_group_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.get_group.side_effect = GroupNotFoundError("missing")

        response = client.get("/rbac/groups/missing")

        assert response.status_code == 404

    def test_update_group(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.update_group.return_value = Group(id="g-1", name="New", description="New", role_ids=[])

        response = client.put(
            "/rbac/groups/g-1",
            json={"name": "New", "description": "New", "role_ids": []},
        )

        assert response.status_code == 200

    def test_update_group_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.update_group.side_effect = GroupNotFoundError("missing")

        response = client.put("/rbac/groups/missing", json={"name": "x", "description": "x", "role_ids": []})

        assert response.status_code == 404

    def test_delete_group(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        response = client.delete("/rbac/groups/g-1")

        assert response.status_code == 204

    def test_delete_group_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.delete_group.side_effect = GroupNotFoundError("missing")

        response = client.delete("/rbac/groups/missing")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# User-Group assignment
# ---------------------------------------------------------------------------


class TestUserGroupAssignment:
    def test_assign_user_to_group(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        response = client.post("/rbac/users/u-1/groups", json={"group_id": "g-1"})

        assert response.status_code == 204
        mock_rbac_service.assign_user_to_group.assert_called_once_with("u-1", "g-1")

    def test_assign_user_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.assign_user_to_group.side_effect = UserNotFoundError("missing")

        response = client.post("/rbac/users/missing/groups", json={"group_id": "g-1"})

        assert response.status_code == 404

    def test_assign_group_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.assign_user_to_group.side_effect = GroupNotFoundError("missing")

        response = client.post("/rbac/users/u-1/groups", json={"group_id": "missing"})

        assert response.status_code == 404

    def test_remove_user_from_group(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        response = client.delete("/rbac/users/u-1/groups/g-1")

        assert response.status_code == 204
        mock_rbac_service.remove_user_from_group.assert_called_once_with("u-1", "g-1")

    def test_remove_user_not_found(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.remove_user_from_group.side_effect = UserNotFoundError("missing")

        response = client.delete("/rbac/users/missing/groups/g-1")

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Resolved permissions
# ---------------------------------------------------------------------------


class TestResolvedPermissionsEndpoint:
    def test_get_resolved_permissions(self, client: TestClient, mock_rbac_service: MagicMock) -> None:
        mock_rbac_service.resolve_permissions.return_value = ["users:read", "users:write"]

        response = client.get("/rbac/users/u-1/permissions")

        assert response.status_code == 200
        data = response.json()
        assert data["user_id"] == "u-1"
        assert data["permissions"] == ["users:read", "users:write"]

    def test_get_resolved_permissions_user_not_found(
        self, client: TestClient, mock_rbac_service: MagicMock
    ) -> None:
        mock_rbac_service.resolve_permissions.side_effect = UserNotFoundError("missing")

        response = client.get("/rbac/users/missing/permissions")

        assert response.status_code == 404

    def test_self_access_allowed_without_users_read(self, mock_rbac_service: MagicMock) -> None:
        """A user can view their own resolved permissions without users:read."""
        from fastapi import FastAPI

        init_rbac_router(mock_rbac_service)
        app = FastAPI()
        app.include_router(rbac_router)

        async def _mock_jwt_auth_no_perms() -> UserContext:
            return UserContext(user_id="user-1", username="testuser", permissions=[])

        app.dependency_overrides[_stub_jwt_auth] = _mock_jwt_auth_no_perms
        client = TestClient(app)

        mock_rbac_service.resolve_permissions.return_value = ["users:read"]

        response = client.get("/rbac/users/user-1/permissions")

        assert response.status_code == 200
        assert response.json()["permissions"] == ["users:read"]

    def test_other_user_access_denied_without_users_read(self, mock_rbac_service: MagicMock) -> None:
        """Cannot view another user's permissions without users:read."""
        from fastapi import FastAPI

        init_rbac_router(mock_rbac_service)
        app = FastAPI()
        app.include_router(rbac_router)

        async def _mock_jwt_auth_no_perms() -> UserContext:
            return UserContext(user_id="user-1", username="testuser", permissions=[])

        app.dependency_overrides[_stub_jwt_auth] = _mock_jwt_auth_no_perms
        client = TestClient(app)

        response = client.get("/rbac/users/other-user/permissions")

        assert response.status_code == 403
