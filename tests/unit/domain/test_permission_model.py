from src.domain.models.permission import Permission


class TestPermissionModel:
    def test_default_values(self) -> None:
        permission = Permission()
        assert permission.id is None
        assert permission.code == ""
        assert permission.description == ""

    def test_custom_values(self) -> None:
        permission = Permission(id="perm-1", code="contracts:read", description="View contracts")
        assert permission.id == "perm-1"
        assert permission.code == "contracts:read"
        assert permission.description == "View contracts"
