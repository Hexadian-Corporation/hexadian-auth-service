from src.domain.models.role import Role


class TestRoleModel:
    def test_default_values(self) -> None:
        role = Role()
        assert role.id is None
        assert role.name == ""
        assert role.description == ""
        assert role.permission_ids == []

    def test_custom_values(self) -> None:
        role = Role(id="role-1", name="Content Manager", description="Manages content", permission_ids=["p1", "p2"])
        assert role.id == "role-1"
        assert role.name == "Content Manager"
        assert role.description == "Manages content"
        assert role.permission_ids == ["p1", "p2"]

    def test_permission_ids_default_factory_isolation(self) -> None:
        role1 = Role()
        role2 = Role()
        role1.permission_ids.append("perm-1")
        assert role2.permission_ids == []
