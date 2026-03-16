from src.domain.models.group import Group


class TestGroupModel:
    def test_default_values(self) -> None:
        group = Group()
        assert group.id is None
        assert group.name == ""
        assert group.description == ""
        assert group.role_ids == []

    def test_custom_values(self) -> None:
        group = Group(id="grp-1", name="Admins", description="Admin group", role_ids=["r1", "r2"])
        assert group.id == "grp-1"
        assert group.name == "Admins"
        assert group.description == "Admin group"
        assert group.role_ids == ["r1", "r2"]

    def test_role_ids_default_factory_isolation(self) -> None:
        group1 = Group()
        group2 = Group()
        group1.role_ids.append("role-1")
        assert group2.role_ids == []
