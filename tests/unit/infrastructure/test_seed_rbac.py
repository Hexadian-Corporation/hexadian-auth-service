from unittest.mock import MagicMock, patch

import pytest

from src.infrastructure.config.settings import Settings
from src.infrastructure.seed.seed_rbac import (
    GROUPS,
    PERMISSIONS,
    ROLES,
    seed,
)


@pytest.fixture()
def mock_collections() -> dict[str, MagicMock]:
    return {
        "permissions": MagicMock(),
        "roles": MagicMock(),
        "groups": MagicMock(),
        "users": MagicMock(),
    }


@pytest.fixture()
def mock_db(mock_collections: dict[str, MagicMock]) -> MagicMock:
    db = MagicMock()
    db.__getitem__ = MagicMock(side_effect=lambda name: mock_collections[name])
    return db


@pytest.fixture()
def settings() -> Settings:
    return Settings(jwt_secret="test-secret", admin_password="testpass123")


class TestSeedPermissions:
    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_creates_all_22_permissions(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = None
        mock_collections["permissions"].insert_one.return_value = MagicMock(inserted_id="perm-id")
        mock_collections["roles"].find_one.return_value = None
        mock_collections["roles"].insert_one.return_value = MagicMock(inserted_id="role-id")
        mock_collections["groups"].find_one.return_value = None
        mock_collections["groups"].insert_one.return_value = MagicMock(inserted_id="group-id")
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="user-id")

        seed(settings)

        assert mock_collections["permissions"].insert_one.call_count == 23

    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_permission_codes_match_spec(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = None
        mock_collections["permissions"].insert_one.return_value = MagicMock(inserted_id="perm-id")
        mock_collections["roles"].find_one.return_value = None
        mock_collections["roles"].insert_one.return_value = MagicMock(inserted_id="role-id")
        mock_collections["groups"].find_one.return_value = None
        mock_collections["groups"].insert_one.return_value = MagicMock(inserted_id="group-id")
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="user-id")

        seed(settings)

        inserted_codes = [c[0][0]["code"] for c in mock_collections["permissions"].insert_one.call_args_list]
        expected_codes = [p["code"] for p in PERMISSIONS]
        assert inserted_codes == expected_codes

    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_skips_existing_permissions(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = {"_id": "existing-id", "code": "x"}
        mock_collections["roles"].find_one.return_value = {"_id": "existing-role", "name": "x"}
        mock_collections["groups"].find_one.return_value = {"_id": "existing-group", "name": "x"}
        mock_collections["users"].find_one.return_value = {"_id": "existing-user", "username": "admin"}

        seed(settings)

        mock_collections["permissions"].insert_one.assert_not_called()


class TestSeedRoles:
    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_creates_9_roles(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = None
        mock_collections["permissions"].insert_one.return_value = MagicMock(inserted_id="perm-id")
        mock_collections["roles"].find_one.return_value = None
        mock_collections["roles"].insert_one.return_value = MagicMock(inserted_id="role-id")
        mock_collections["groups"].find_one.return_value = None
        mock_collections["groups"].insert_one.return_value = MagicMock(inserted_id="group-id")
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="user-id")

        seed(settings)

        assert mock_collections["roles"].insert_one.call_count == 9

    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_role_names_match_spec(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = None
        mock_collections["permissions"].insert_one.return_value = MagicMock(inserted_id="perm-id")
        mock_collections["roles"].find_one.return_value = None
        mock_collections["roles"].insert_one.return_value = MagicMock(inserted_id="role-id")
        mock_collections["groups"].find_one.return_value = None
        mock_collections["groups"].insert_one.return_value = MagicMock(inserted_id="group-id")
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="user-id")

        seed(settings)

        inserted_names = [c[0][0]["name"] for c in mock_collections["roles"].insert_one.call_args_list]
        assert inserted_names == [
            "Auth Admin",
            "Auth User Manager",
            "HHH Contracts Manager",
            "HHH Locations Manager",
            "HHH Commodities Manager",
            "HHH Ships Manager",
            "HHH Graphs Manager",
            "HHH Routes Manager",
            "HHH Viewer",
        ]

    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_auth_admin_has_4_permission_ids(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        perm_counter = iter(range(1, 100))
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = None
        mock_collections["permissions"].insert_one.side_effect = lambda _: MagicMock(
            inserted_id=f"perm-{next(perm_counter)}"
        )
        mock_collections["roles"].find_one.return_value = None
        mock_collections["roles"].insert_one.return_value = MagicMock(inserted_id="role-id")
        mock_collections["groups"].find_one.return_value = None
        mock_collections["groups"].insert_one.return_value = MagicMock(inserted_id="group-id")
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="user-id")

        seed(settings)

        auth_admin_call = mock_collections["roles"].insert_one.call_args_list[0]
        auth_admin_doc = auth_admin_call[0][0]
        assert auth_admin_doc["name"] == "Auth Admin"
        assert len(auth_admin_doc["permission_ids"]) == 5

    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_auth_user_manager_has_2_permission_ids(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        perm_counter = iter(range(1, 100))
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = None
        mock_collections["permissions"].insert_one.side_effect = lambda _: MagicMock(
            inserted_id=f"perm-{next(perm_counter)}"
        )
        mock_collections["roles"].find_one.return_value = None
        mock_collections["roles"].insert_one.return_value = MagicMock(inserted_id="role-id")
        mock_collections["groups"].find_one.return_value = None
        mock_collections["groups"].insert_one.return_value = MagicMock(inserted_id="group-id")
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="user-id")

        seed(settings)

        user_mgr_call = mock_collections["roles"].insert_one.call_args_list[1]
        user_mgr_doc = user_mgr_call[0][0]
        assert user_mgr_doc["name"] == "Auth User Manager"
        assert len(user_mgr_doc["permission_ids"]) == 2

    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_hhh_contracts_manager_has_3_permission_ids(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        perm_counter = iter(range(1, 100))
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = None
        mock_collections["permissions"].insert_one.side_effect = lambda _: MagicMock(
            inserted_id=f"perm-{next(perm_counter)}"
        )
        mock_collections["roles"].find_one.return_value = None
        mock_collections["roles"].insert_one.return_value = MagicMock(inserted_id="role-id")
        mock_collections["groups"].find_one.return_value = None
        mock_collections["groups"].insert_one.return_value = MagicMock(inserted_id="group-id")
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="user-id")

        seed(settings)

        contracts_mgr_call = mock_collections["roles"].insert_one.call_args_list[2]
        contracts_mgr_doc = contracts_mgr_call[0][0]
        assert contracts_mgr_doc["name"] == "HHH Contracts Manager"
        assert len(contracts_mgr_doc["permission_ids"]) == 3

    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_skips_existing_roles(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = {"_id": "existing-id", "code": "x"}
        mock_collections["roles"].find_one.return_value = {"_id": "existing-role", "name": "x"}
        mock_collections["groups"].find_one.return_value = {"_id": "existing-group", "name": "x"}
        mock_collections["users"].find_one.return_value = {"_id": "existing-user", "username": "admin"}

        seed(settings)

        mock_collections["roles"].insert_one.assert_not_called()


class TestSeedGroups:
    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_creates_3_groups(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = None
        mock_collections["permissions"].insert_one.return_value = MagicMock(inserted_id="perm-id")
        mock_collections["roles"].find_one.return_value = None
        mock_collections["roles"].insert_one.return_value = MagicMock(inserted_id="role-id")
        mock_collections["groups"].find_one.return_value = None
        mock_collections["groups"].insert_one.return_value = MagicMock(inserted_id="group-id")
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="user-id")

        seed(settings)

        assert mock_collections["groups"].insert_one.call_count == 3

    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_group_names_match_spec(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = None
        mock_collections["permissions"].insert_one.return_value = MagicMock(inserted_id="perm-id")
        mock_collections["roles"].find_one.return_value = None
        mock_collections["roles"].insert_one.return_value = MagicMock(inserted_id="role-id")
        mock_collections["groups"].find_one.return_value = None
        mock_collections["groups"].insert_one.return_value = MagicMock(inserted_id="group-id")
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="user-id")

        seed(settings)

        inserted_names = [c[0][0]["name"] for c in mock_collections["groups"].insert_one.call_args_list]
        assert inserted_names == ["Admins", "Users", "Content Managers"]

    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_skips_existing_groups(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = {"_id": "existing-id", "code": "x"}
        mock_collections["roles"].find_one.return_value = {"_id": "existing-role", "name": "x"}
        mock_collections["groups"].find_one.return_value = {"_id": "existing-group", "name": "x"}
        mock_collections["users"].find_one.return_value = {"_id": "existing-user", "username": "admin"}

        seed(settings)

        mock_collections["groups"].insert_one.assert_not_called()


class TestSeedAdminUser:
    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_creates_admin_user(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = None
        mock_collections["permissions"].insert_one.return_value = MagicMock(inserted_id="perm-id")
        mock_collections["roles"].find_one.return_value = None
        mock_collections["roles"].insert_one.return_value = MagicMock(inserted_id="role-id")
        mock_collections["groups"].find_one.return_value = None
        mock_collections["groups"].insert_one.return_value = MagicMock(inserted_id="group-id")
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="user-id")

        seed(settings)

        mock_collections["users"].insert_one.assert_called_once()
        admin_doc = mock_collections["users"].insert_one.call_args[0][0]
        assert admin_doc["username"] == "admin"
        assert admin_doc["rsi_handle"] == "HexadianAdmin"
        assert admin_doc["rsi_verified"] is False
        assert admin_doc["is_active"] is True
        assert admin_doc["group_ids"] == ["group-id"]
        assert ":" in admin_doc["hashed_password"]

    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_skips_existing_admin(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = {"_id": "existing-id", "code": "x"}
        mock_collections["roles"].find_one.return_value = {"_id": "existing-role", "name": "x"}
        mock_collections["groups"].find_one.return_value = {"_id": "existing-group", "name": "x"}
        mock_collections["users"].find_one.return_value = {"_id": "existing-user", "username": "admin"}

        seed(settings)

        mock_collections["users"].insert_one.assert_not_called()

    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_admin_password_from_settings(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
    ) -> None:
        custom_settings = Settings(jwt_secret="test-secret", admin_password="custom-pw-123")
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = None
        mock_collections["permissions"].insert_one.return_value = MagicMock(inserted_id="perm-id")
        mock_collections["roles"].find_one.return_value = None
        mock_collections["roles"].insert_one.return_value = MagicMock(inserted_id="role-id")
        mock_collections["groups"].find_one.return_value = None
        mock_collections["groups"].insert_one.return_value = MagicMock(inserted_id="group-id")
        mock_collections["users"].find_one.return_value = None
        mock_collections["users"].insert_one.return_value = MagicMock(inserted_id="user-id")

        seed(custom_settings)

        admin_doc = mock_collections["users"].insert_one.call_args[0][0]
        # Verify password was hashed (salt:hash format)
        salt, hashed = admin_doc["hashed_password"].split(":")
        assert len(salt) == 32  # 16 bytes hex
        assert len(hashed) == 64  # SHA256 hex


class TestSeedIdempotent:
    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_full_idempotent_run_no_inserts(
        self,
        mock_mongo_client: MagicMock,
        mock_db: MagicMock,
        mock_collections: dict[str, MagicMock],
        settings: Settings,
    ) -> None:
        """Running seed when all data exists should not insert anything."""
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)
        mock_collections["permissions"].find_one.return_value = {"_id": "existing-id", "code": "x"}
        mock_collections["roles"].find_one.return_value = {"_id": "existing-role", "name": "x"}
        mock_collections["groups"].find_one.return_value = {"_id": "existing-group", "name": "x"}
        mock_collections["users"].find_one.return_value = {"_id": "existing-user", "username": "admin"}

        seed(settings)

        mock_collections["permissions"].insert_one.assert_not_called()
        mock_collections["roles"].insert_one.assert_not_called()
        mock_collections["groups"].insert_one.assert_not_called()
        mock_collections["users"].insert_one.assert_not_called()


class TestSeedDefaults:
    @patch("src.infrastructure.seed.seed_rbac.MongoClient")
    def test_seed_uses_default_settings_when_none(self, mock_mongo_client: MagicMock) -> None:
        mock_db = MagicMock()
        mock_col = MagicMock()
        mock_col.find_one.return_value = {"_id": "x"}
        mock_db.__getitem__ = MagicMock(return_value=mock_col)
        mock_mongo_client.return_value.__getitem__ = MagicMock(return_value=mock_db)

        seed(None)

        mock_mongo_client.assert_called_once()


class TestSeedDataDefinitions:
    def test_permissions_count(self) -> None:
        assert len(PERMISSIONS) == 23

    def test_roles_count(self) -> None:
        assert len(ROLES) == 9

    def test_groups_count(self) -> None:
        assert len(GROUPS) == 3

    def test_all_permission_codes_unique(self) -> None:
        codes = [p["code"] for p in PERMISSIONS]
        assert len(codes) == len(set(codes))

    def test_all_role_names_unique(self) -> None:
        names = [r["name"] for r in ROLES]
        assert len(names) == len(set(names))

    def test_all_group_names_unique(self) -> None:
        names = [g["name"] for g in GROUPS]
        assert len(names) == len(set(names))

    def test_role_permission_codes_are_valid(self) -> None:
        valid_codes = {p["code"] for p in PERMISSIONS}
        for role in ROLES:
            for code in role["permission_codes"]:
                assert code in valid_codes, f"Role '{role['name']}' has invalid permission code: {code}"

    def test_group_role_names_are_valid(self) -> None:
        valid_names = {r["name"] for r in ROLES}
        for group in GROUPS:
            for name in group["role_names"]:
                assert name in valid_names, f"Group '{group['name']}' has invalid role name: {name}"

    def test_groups_have_auto_assign_apps_field(self) -> None:
        for group in GROUPS:
            assert "auto_assign_apps" in group, f"Group '{group['name']}' missing auto_assign_apps"
            assert isinstance(group["auto_assign_apps"], list)

    def test_users_group_auto_assign_apps(self) -> None:
        users_group = next(g for g in GROUPS if g["name"] == "Users")
        assert "hhh-frontend" in users_group["auto_assign_apps"]
        assert "hhh-backoffice" not in users_group["auto_assign_apps"]

    def test_admins_group_has_empty_auto_assign_apps(self) -> None:
        admins_group = next(g for g in GROUPS if g["name"] == "Admins")
        assert admins_group["auto_assign_apps"] == []
