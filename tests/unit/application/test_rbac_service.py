from unittest.mock import MagicMock

import pytest

from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.permission_repository import PermissionRepository
from src.application.ports.outbound.role_repository import RoleRepository
from src.application.ports.outbound.user_repository import UserRepository
from src.application.services.rbac_service_impl import RbacServiceImpl
from src.domain.exceptions.group_exceptions import GroupNotFoundError
from src.domain.exceptions.permission_exceptions import PermissionNotFoundError
from src.domain.exceptions.role_exceptions import RoleNotFoundError
from src.domain.exceptions.user_exceptions import UserNotFoundError
from src.domain.models.group import Group
from src.domain.models.permission import Permission
from src.domain.models.role import Role
from src.domain.models.user import User


@pytest.fixture()
def mock_user_repository() -> MagicMock:
    return MagicMock(spec=UserRepository)


@pytest.fixture()
def mock_permission_repository() -> MagicMock:
    return MagicMock(spec=PermissionRepository)


@pytest.fixture()
def mock_role_repository() -> MagicMock:
    return MagicMock(spec=RoleRepository)


@pytest.fixture()
def mock_group_repository() -> MagicMock:
    return MagicMock(spec=GroupRepository)


@pytest.fixture()
def service(
    mock_user_repository: MagicMock,
    mock_permission_repository: MagicMock,
    mock_role_repository: MagicMock,
    mock_group_repository: MagicMock,
) -> RbacServiceImpl:
    return RbacServiceImpl(
        user_repository=mock_user_repository,
        permission_repository=mock_permission_repository,
        role_repository=mock_role_repository,
        group_repository=mock_group_repository,
    )


# ---------------------------------------------------------------------------
# Permission CRUD
# ---------------------------------------------------------------------------


class TestCreatePermission:
    def test_creates_and_returns_permission(
        self, service: RbacServiceImpl, mock_permission_repository: MagicMock
    ) -> None:
        mock_permission_repository.save.side_effect = lambda p: Permission(
            id="p-1", code=p.code, description=p.description
        )

        result = service.create_permission("users:read", "Read users")

        assert result.id == "p-1"
        assert result.code == "users:read"
        assert result.description == "Read users"
        mock_permission_repository.save.assert_called_once()


class TestGetPermission:
    def test_returns_permission_when_found(
        self, service: RbacServiceImpl, mock_permission_repository: MagicMock
    ) -> None:
        mock_permission_repository.find_by_id.return_value = Permission(id="p-1", code="users:read", description="Read")

        result = service.get_permission("p-1")

        assert result.id == "p-1"

    def test_raises_when_not_found(self, service: RbacServiceImpl, mock_permission_repository: MagicMock) -> None:
        mock_permission_repository.find_by_id.return_value = None

        with pytest.raises(PermissionNotFoundError):
            service.get_permission("missing")


class TestListPermissions:
    def test_returns_all_permissions(self, service: RbacServiceImpl, mock_permission_repository: MagicMock) -> None:
        mock_permission_repository.find_all.return_value = [
            Permission(id="p-1", code="a", description="A"),
            Permission(id="p-2", code="b", description="B"),
        ]

        result = service.list_permissions()

        assert len(result) == 2


class TestUpdatePermission:
    def test_updates_and_returns_permission(
        self, service: RbacServiceImpl, mock_permission_repository: MagicMock
    ) -> None:
        existing = Permission(id="p-1", code="old", description="Old")
        mock_permission_repository.find_by_id.return_value = existing
        mock_permission_repository.save.side_effect = lambda p: p

        result = service.update_permission("p-1", "new", "New")

        assert result.code == "new"
        assert result.description == "New"

    def test_raises_when_not_found(self, service: RbacServiceImpl, mock_permission_repository: MagicMock) -> None:
        mock_permission_repository.find_by_id.return_value = None

        with pytest.raises(PermissionNotFoundError):
            service.update_permission("missing", "x", "X")


class TestDeletePermission:
    def test_deletes_successfully(self, service: RbacServiceImpl, mock_permission_repository: MagicMock) -> None:
        mock_permission_repository.delete.return_value = True

        service.delete_permission("p-1")

        mock_permission_repository.delete.assert_called_once_with("p-1")

    def test_raises_when_not_found(self, service: RbacServiceImpl, mock_permission_repository: MagicMock) -> None:
        mock_permission_repository.delete.return_value = False

        with pytest.raises(PermissionNotFoundError):
            service.delete_permission("missing")


# ---------------------------------------------------------------------------
# Role CRUD
# ---------------------------------------------------------------------------


class TestCreateRole:
    def test_creates_and_returns_role(self, service: RbacServiceImpl, mock_role_repository: MagicMock) -> None:
        mock_role_repository.save.side_effect = lambda r: Role(
            id="r-1", name=r.name, description=r.description, permission_ids=r.permission_ids
        )

        result = service.create_role("Admin", "Admin role", ["p-1", "p-2"])

        assert result.id == "r-1"
        assert result.name == "Admin"
        assert result.permission_ids == ["p-1", "p-2"]


class TestGetRole:
    def test_returns_role_when_found(self, service: RbacServiceImpl, mock_role_repository: MagicMock) -> None:
        mock_role_repository.find_by_id.return_value = Role(id="r-1", name="Admin")

        result = service.get_role("r-1")

        assert result.id == "r-1"

    def test_raises_when_not_found(self, service: RbacServiceImpl, mock_role_repository: MagicMock) -> None:
        mock_role_repository.find_by_id.return_value = None

        with pytest.raises(RoleNotFoundError):
            service.get_role("missing")


class TestListRoles:
    def test_returns_all_roles(self, service: RbacServiceImpl, mock_role_repository: MagicMock) -> None:
        mock_role_repository.find_all.return_value = [Role(id="r-1"), Role(id="r-2")]

        result = service.list_roles()

        assert len(result) == 2


class TestUpdateRole:
    def test_updates_and_returns_role(self, service: RbacServiceImpl, mock_role_repository: MagicMock) -> None:
        existing = Role(id="r-1", name="Old", description="Old", permission_ids=["p-1"])
        mock_role_repository.find_by_id.return_value = existing
        mock_role_repository.save.side_effect = lambda r: r

        result = service.update_role("r-1", "New", "New desc", ["p-2"])

        assert result.name == "New"
        assert result.permission_ids == ["p-2"]

    def test_raises_when_not_found(self, service: RbacServiceImpl, mock_role_repository: MagicMock) -> None:
        mock_role_repository.find_by_id.return_value = None

        with pytest.raises(RoleNotFoundError):
            service.update_role("missing", "x", "x", [])


class TestDeleteRole:
    def test_deletes_successfully(self, service: RbacServiceImpl, mock_role_repository: MagicMock) -> None:
        mock_role_repository.delete.return_value = True

        service.delete_role("r-1")

        mock_role_repository.delete.assert_called_once_with("r-1")

    def test_raises_when_not_found(self, service: RbacServiceImpl, mock_role_repository: MagicMock) -> None:
        mock_role_repository.delete.return_value = False

        with pytest.raises(RoleNotFoundError):
            service.delete_role("missing")


# ---------------------------------------------------------------------------
# Group CRUD
# ---------------------------------------------------------------------------


class TestCreateGroup:
    def test_creates_and_returns_group(self, service: RbacServiceImpl, mock_group_repository: MagicMock) -> None:
        mock_group_repository.save.side_effect = lambda g: Group(
            id="g-1", name=g.name, description=g.description, role_ids=g.role_ids
        )

        result = service.create_group("Admins", "Admin group", ["r-1"])

        assert result.id == "g-1"
        assert result.name == "Admins"
        assert result.role_ids == ["r-1"]

    def test_creates_group_with_auto_assign_apps(
        self, service: RbacServiceImpl, mock_group_repository: MagicMock
    ) -> None:
        mock_group_repository.save.side_effect = lambda g: g

        result = service.create_group("Users", "Users group", ["r-1"], auto_assign_apps=["hhh-frontend"])

        assert result.auto_assign_apps == ["hhh-frontend"]

    def test_creates_group_without_auto_assign_apps_defaults_to_empty(
        self, service: RbacServiceImpl, mock_group_repository: MagicMock
    ) -> None:
        mock_group_repository.save.side_effect = lambda g: g

        result = service.create_group("Admins", "Admin group", ["r-1"])

        assert result.auto_assign_apps == []


class TestGetGroup:
    def test_returns_group_when_found(self, service: RbacServiceImpl, mock_group_repository: MagicMock) -> None:
        mock_group_repository.find_by_id.return_value = Group(id="g-1", name="Admins")

        result = service.get_group("g-1")

        assert result.id == "g-1"

    def test_raises_when_not_found(self, service: RbacServiceImpl, mock_group_repository: MagicMock) -> None:
        mock_group_repository.find_by_id.return_value = None

        with pytest.raises(GroupNotFoundError):
            service.get_group("missing")


class TestListGroups:
    def test_returns_all_groups(self, service: RbacServiceImpl, mock_group_repository: MagicMock) -> None:
        mock_group_repository.find_all.return_value = [Group(id="g-1"), Group(id="g-2")]

        result = service.list_groups()

        assert len(result) == 2


class TestUpdateGroup:
    def test_updates_and_returns_group(self, service: RbacServiceImpl, mock_group_repository: MagicMock) -> None:
        existing = Group(id="g-1", name="Old", description="Old", role_ids=["r-1"])
        mock_group_repository.find_by_id.return_value = existing
        mock_group_repository.save.side_effect = lambda g: g

        result = service.update_group("g-1", "New", "New desc", ["r-2"])

        assert result.name == "New"
        assert result.role_ids == ["r-2"]

    def test_updates_group_with_auto_assign_apps(
        self, service: RbacServiceImpl, mock_group_repository: MagicMock
    ) -> None:
        existing = Group(id="g-1", name="Users", description="Users", role_ids=["r-1"], auto_assign_apps=[])
        mock_group_repository.find_by_id.return_value = existing
        mock_group_repository.save.side_effect = lambda g: g

        result = service.update_group("g-1", "Users", "Users", ["r-1"], auto_assign_apps=["hhh-frontend"])

        assert result.auto_assign_apps == ["hhh-frontend"]

    def test_updates_group_without_auto_assign_apps_preserves_existing(
        self, service: RbacServiceImpl, mock_group_repository: MagicMock
    ) -> None:
        existing = Group(
            id="g-1", name="Users", description="Users", role_ids=["r-1"], auto_assign_apps=["hhh-frontend"]
        )
        mock_group_repository.find_by_id.return_value = existing
        mock_group_repository.save.side_effect = lambda g: g

        result = service.update_group("g-1", "Users", "Updated desc", ["r-1"])

        assert result.auto_assign_apps == ["hhh-frontend"]

    def test_raises_when_not_found(self, service: RbacServiceImpl, mock_group_repository: MagicMock) -> None:
        mock_group_repository.find_by_id.return_value = None

        with pytest.raises(GroupNotFoundError):
            service.update_group("missing", "x", "x", [])


class TestDeleteGroup:
    def test_deletes_successfully(self, service: RbacServiceImpl, mock_group_repository: MagicMock) -> None:
        mock_group_repository.delete.return_value = True

        service.delete_group("g-1")

        mock_group_repository.delete.assert_called_once_with("g-1")

    def test_raises_when_not_found(self, service: RbacServiceImpl, mock_group_repository: MagicMock) -> None:
        mock_group_repository.delete.return_value = False

        with pytest.raises(GroupNotFoundError):
            service.delete_group("missing")


# ---------------------------------------------------------------------------
# Permission resolution
# ---------------------------------------------------------------------------


class TestResolvePermissions:
    def test_resolves_user_group_role_permission_chain(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
        mock_group_repository: MagicMock,
        mock_role_repository: MagicMock,
        mock_permission_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=["g-1"])
        mock_user_repository.find_by_id.return_value = user

        mock_group_repository.find_by_ids.return_value = [Group(id="g-1", role_ids=["r-1"])]
        mock_role_repository.find_by_ids.return_value = [Role(id="r-1", permission_ids=["p-1", "p-2"])]
        mock_permission_repository.find_by_ids.return_value = [
            Permission(id="p-1", code="users:read"),
            Permission(id="p-2", code="users:write"),
        ]

        result = service.resolve_permissions("u-1")

        assert result == ["users:read", "users:write"]

    def test_deduplicates_permissions_from_overlapping_roles(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
        mock_group_repository: MagicMock,
        mock_role_repository: MagicMock,
        mock_permission_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=["g-1", "g-2"])
        mock_user_repository.find_by_id.return_value = user

        mock_group_repository.find_by_ids.return_value = [
            Group(id="g-1", role_ids=["r-1"]),
            Group(id="g-2", role_ids=["r-2"]),
        ]
        mock_role_repository.find_by_ids.return_value = [
            Role(id="r-1", permission_ids=["p-1", "p-2"]),
            Role(id="r-2", permission_ids=["p-2", "p-3"]),
        ]
        mock_permission_repository.find_by_ids.return_value = [
            Permission(id="p-1", code="users:read"),
            Permission(id="p-2", code="users:write"),
            Permission(id="p-2b", code="users:write"),
            Permission(id="p-3", code="users:admin"),
        ]

        result = service.resolve_permissions("u-1")

        assert result == ["users:read", "users:write", "users:admin"]

    def test_returns_empty_list_when_user_has_no_groups(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=[])
        mock_user_repository.find_by_id.return_value = user

        result = service.resolve_permissions("u-1")

        assert result == []

    def test_returns_empty_list_when_groups_have_no_roles(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=["g-1"])
        mock_user_repository.find_by_id.return_value = user
        mock_group_repository.find_by_ids.return_value = [Group(id="g-1", role_ids=[])]

        result = service.resolve_permissions("u-1")

        assert result == []

    def test_returns_empty_list_when_roles_have_no_permissions(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
        mock_group_repository: MagicMock,
        mock_role_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=["g-1"])
        mock_user_repository.find_by_id.return_value = user
        mock_group_repository.find_by_ids.return_value = [Group(id="g-1", role_ids=["r-1"])]
        mock_role_repository.find_by_ids.return_value = [Role(id="r-1", permission_ids=[])]

        result = service.resolve_permissions("u-1")

        assert result == []

    def test_raises_when_user_not_found(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
    ) -> None:
        mock_user_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            service.resolve_permissions("missing")


# ---------------------------------------------------------------------------
# User-Group assignment
# ---------------------------------------------------------------------------


class TestAssignUserToGroup:
    def test_adds_group_id_to_user(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=[])
        mock_user_repository.find_by_id.return_value = user
        mock_group_repository.find_by_id.return_value = Group(id="g-1", name="Admins")
        mock_user_repository.save.side_effect = lambda u: u

        service.assign_user_to_group("u-1", "g-1")

        assert "g-1" in user.group_ids
        mock_user_repository.save.assert_called_once()

    def test_does_not_duplicate_group_id(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=["g-1"])
        mock_user_repository.find_by_id.return_value = user
        mock_group_repository.find_by_id.return_value = Group(id="g-1", name="Admins")

        service.assign_user_to_group("u-1", "g-1")

        assert user.group_ids == ["g-1"]
        mock_user_repository.save.assert_not_called()

    def test_raises_when_user_not_found(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
    ) -> None:
        mock_user_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            service.assign_user_to_group("missing", "g-1")

    def test_raises_when_group_not_found(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=[])
        mock_user_repository.find_by_id.return_value = user
        mock_group_repository.find_by_id.return_value = None

        with pytest.raises(GroupNotFoundError):
            service.assign_user_to_group("u-1", "missing")


class TestRemoveUserFromGroup:
    def test_removes_group_id_from_user(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=["g-1", "g-2"])
        mock_user_repository.find_by_id.return_value = user
        mock_user_repository.save.side_effect = lambda u: u

        service.remove_user_from_group("u-1", "g-1")

        assert "g-1" not in user.group_ids
        assert "g-2" in user.group_ids
        mock_user_repository.save.assert_called_once()

    def test_no_op_when_group_id_not_present(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=["g-2"])
        mock_user_repository.find_by_id.return_value = user

        service.remove_user_from_group("u-1", "g-1")

        assert user.group_ids == ["g-2"]
        mock_user_repository.save.assert_not_called()

    def test_raises_when_user_not_found(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
    ) -> None:
        mock_user_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            service.remove_user_from_group("missing", "g-1")


# ---------------------------------------------------------------------------
# RBAC claims resolution
# ---------------------------------------------------------------------------


class TestResolveRbacClaims:
    def test_resolves_full_claims(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
        mock_group_repository: MagicMock,
        mock_role_repository: MagicMock,
        mock_permission_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=["g-1"])
        mock_user_repository.find_by_id.return_value = user
        mock_group_repository.find_by_ids.return_value = [Group(id="g-1", name="Admins", role_ids=["r-1"])]
        mock_role_repository.find_by_ids.return_value = [Role(id="r-1", name="Super Admin", permission_ids=["p-1"])]
        mock_permission_repository.find_by_ids.return_value = [Permission(id="p-1", code="users:admin")]

        result = service.resolve_rbac_claims("u-1")

        assert result.groups == ["Admins"]
        assert result.roles == ["Super Admin"]
        assert result.permissions == ["users:admin"]

    def test_returns_empty_claims_when_no_groups(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=[])
        mock_user_repository.find_by_id.return_value = user

        result = service.resolve_rbac_claims("u-1")

        assert result.groups == []
        assert result.roles == []
        assert result.permissions == []

    def test_returns_groups_only_when_no_roles(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
        mock_group_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=["g-1"])
        mock_user_repository.find_by_id.return_value = user
        mock_group_repository.find_by_ids.return_value = [Group(id="g-1", name="Empty Group", role_ids=[])]

        result = service.resolve_rbac_claims("u-1")

        assert result.groups == ["Empty Group"]
        assert result.roles == []
        assert result.permissions == []

    def test_returns_groups_and_roles_when_no_permissions(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
        mock_group_repository: MagicMock,
        mock_role_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=["g-1"])
        mock_user_repository.find_by_id.return_value = user
        mock_group_repository.find_by_ids.return_value = [Group(id="g-1", name="Admins", role_ids=["r-1"])]
        mock_role_repository.find_by_ids.return_value = [Role(id="r-1", name="Empty Role", permission_ids=[])]

        result = service.resolve_rbac_claims("u-1")

        assert result.groups == ["Admins"]
        assert result.roles == ["Empty Role"]
        assert result.permissions == []

    def test_deduplicates_roles_and_permissions(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
        mock_group_repository: MagicMock,
        mock_role_repository: MagicMock,
        mock_permission_repository: MagicMock,
    ) -> None:
        user = User(id="u-1", username="testuser", group_ids=["g-1", "g-2"])
        mock_user_repository.find_by_id.return_value = user
        mock_group_repository.find_by_ids.return_value = [
            Group(id="g-1", name="Admins", role_ids=["r-1"]),
            Group(id="g-2", name="Users", role_ids=["r-1", "r-2"]),
        ]
        mock_role_repository.find_by_ids.return_value = [
            Role(id="r-1", name="Super Admin", permission_ids=["p-1", "p-2"]),
            Role(id="r-1b", name="Super Admin", permission_ids=["p-1"]),
            Role(id="r-2", name="Member", permission_ids=["p-1"]),
        ]
        mock_permission_repository.find_by_ids.return_value = [
            Permission(id="p-1", code="contracts:read"),
            Permission(id="p-2", code="contracts:write"),
            Permission(id="p-1b", code="contracts:read"),
        ]

        result = service.resolve_rbac_claims("u-1")

        assert result.groups == ["Admins", "Users"]
        assert result.roles == ["Super Admin", "Member"]
        assert result.permissions == ["contracts:read", "contracts:write"]

    def test_raises_when_user_not_found(
        self,
        service: RbacServiceImpl,
        mock_user_repository: MagicMock,
    ) -> None:
        mock_user_repository.find_by_id.return_value = None

        with pytest.raises(UserNotFoundError):
            service.resolve_rbac_claims("missing")
