from src.domain.models.user import User


class TestUserModelGroupIds:
    def test_default_group_ids_is_empty_list(self) -> None:
        user = User()
        assert user.group_ids == []

    def test_custom_group_ids(self) -> None:
        user = User(group_ids=["grp-1", "grp-2"])
        assert user.group_ids == ["grp-1", "grp-2"]

    def test_group_ids_default_factory_isolation(self) -> None:
        user1 = User()
        user2 = User()
        user1.group_ids.append("grp-1")
        assert user2.group_ids == []

    def test_user_no_longer_has_roles_attribute(self) -> None:
        user = User()
        assert not hasattr(user, "roles")
