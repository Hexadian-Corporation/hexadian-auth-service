from src.domain.exceptions.group_exceptions import GroupNotFoundError
from src.domain.exceptions.permission_exceptions import PermissionNotFoundError
from src.domain.exceptions.role_exceptions import RoleNotFoundError


class TestPermissionNotFoundError:
    def test_message_contains_id(self) -> None:
        error = PermissionNotFoundError("perm-123")
        assert "perm-123" in str(error)

    def test_stores_permission_id(self) -> None:
        error = PermissionNotFoundError("perm-123")
        assert error.permission_id == "perm-123"


class TestRoleNotFoundError:
    def test_message_contains_id(self) -> None:
        error = RoleNotFoundError("role-123")
        assert "role-123" in str(error)

    def test_stores_role_id(self) -> None:
        error = RoleNotFoundError("role-123")
        assert error.role_id == "role-123"


class TestGroupNotFoundError:
    def test_message_contains_id(self) -> None:
        error = GroupNotFoundError("grp-123")
        assert "grp-123" in str(error)

    def test_stores_group_id(self) -> None:
        error = GroupNotFoundError("grp-123")
        assert error.group_id == "grp-123"
