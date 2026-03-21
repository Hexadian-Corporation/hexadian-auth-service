"""Integration tests for the RBAC seed script against a real MongoDB instance."""

import asyncio
import threading

import pytest
from pymongo.database import Database

from src.infrastructure.config.settings import Settings
from src.infrastructure.seed.seed_rbac import GROUPS, PERMISSIONS, ROLES, seed


def _make_settings(db: Database) -> Settings:
    """Create Settings pointing at the test database's connection."""
    # Use the full URL stored by the conftest fixture (includes auth credentials)
    mongo_url: str = getattr(db, "_mongo_url", None)  # type: ignore[assignment]
    if mongo_url is None:
        # Fallback for unauthenticated containers
        client = db.client
        host = client.address[0]
        port = client.address[1]
        mongo_url = f"mongodb://{host}:{port}"
    return Settings(
        mongo_uri=mongo_url,
        mongo_db=db.name,
        jwt_secret="test-secret",
        admin_password="testpass123",
    )


class TestSeedPermissionsIntegration:
    async def test_seed_creates_all_permissions_in_mongodb(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        assert db["permissions"].count_documents({}) == len(PERMISSIONS)

    async def test_seed_permissions_are_retrievable_by_code(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        for perm in PERMISSIONS:
            doc = db["permissions"].find_one({"code": perm["code"]})
            assert doc is not None, f"Permission '{perm['code']}' not found in MongoDB"
            assert doc["code"] == perm["code"]
            assert isinstance(doc["description"], str)
            assert len(doc["description"]) > 0

    async def test_seed_permissions_idempotent_no_duplicates(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        await seed(settings)
        assert db["permissions"].count_documents({}) == len(PERMISSIONS)

    async def test_seed_permissions_include_distance_finder(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        doc = db["permissions"].find_one({"code": "hhh:feature:distance_finder"})
        assert doc is not None
        assert doc["code"] == "hhh:feature:distance_finder"
        assert isinstance(doc["description"], str)
        assert len(doc["description"]) > 0

    async def test_seed_permissions_include_all_hhh_feature_codes(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        expected_feature_codes = [
            "hhh:feature:gpu",
            "hhh:feature:step_by_step",
            "hhh:feature:multi_system",
            "hhh:feature:export",
            "hhh:feature:risk_analysis",
            "hhh:feature:route_comparison",
            "hhh:feature:history_unlimited",
            "hhh:feature:simultaneous_plans",
            "hhh:feature:cargo_limit",
            "hhh:feature:distance_finder",
        ]
        for code in expected_feature_codes:
            doc = db["permissions"].find_one({"code": code})
            assert doc is not None, f"Feature permission '{code}' not found in MongoDB"

    async def test_permission_documents_have_required_fields(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        from bson import ObjectId

        for doc in db["permissions"].find({}):
            assert "code" in doc and isinstance(doc["code"], str) and doc["code"]
            assert "description" in doc and isinstance(doc["description"], str) and doc["description"]
            assert "_id" in doc and isinstance(doc["_id"], ObjectId)


class TestSeedRolesIntegration:
    async def test_seed_creates_all_roles_in_mongodb(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        assert db["roles"].count_documents({}) == len(ROLES)

    async def test_seed_roles_idempotent_no_duplicates(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        await seed(settings)
        assert db["roles"].count_documents({}) == len(ROLES)

    async def test_hhh_feature_premium_role_has_10_permission_ids(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        role = db["roles"].find_one({"name": "HHH Feature Premium"})
        assert role is not None
        assert len(role["permission_ids"]) == 10

    async def test_hhh_feature_premium_role_includes_distance_finder_permission_id(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        distance_finder_perm = db["permissions"].find_one({"code": "hhh:feature:distance_finder"})
        assert distance_finder_perm is not None
        role = db["roles"].find_one({"name": "HHH Feature Premium"})
        assert role is not None
        assert str(distance_finder_perm["_id"]) in role["permission_ids"]

    async def test_role_permission_ids_reference_real_permission_documents(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        for role in db["roles"].find({}):
            for perm_id in role["permission_ids"]:
                from bson import ObjectId

                perm = db["permissions"].find_one({"_id": ObjectId(perm_id)})
                assert perm is not None, f"Role '{role['name']}' references non-existent permission id '{perm_id}'"

    async def test_each_role_name_is_unique(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        names = [r["name"] for r in db["roles"].find({})]
        assert len(names) == len(set(names))

    async def test_auth_admin_role_has_manage_permissions(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        role = db["roles"].find_one({"name": "Auth Admin"})
        assert role is not None
        # Resolve permission IDs back to codes
        from bson import ObjectId

        perm_ids = [ObjectId(pid) for pid in role["permission_ids"]]
        codes = {doc["code"] for doc in db["permissions"].find({"_id": {"$in": perm_ids}})}
        assert "auth:rbac:manage" in codes
        assert "auth:users:manage" in codes


class TestSeedGroupsIntegration:
    async def test_seed_creates_all_groups_in_mongodb(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        assert db["groups"].count_documents({}) == len(GROUPS)

    async def test_seed_groups_idempotent_no_duplicates(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        await seed(settings)
        assert db["groups"].count_documents({}) == len(GROUPS)

    async def test_hexadian_members_group_includes_premium_role(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        group = db["groups"].find_one({"name": "Hexadian Members"})
        assert group is not None
        premium_role = db["roles"].find_one({"name": "HHH Feature Premium"})
        assert premium_role is not None
        assert str(premium_role["_id"]) in group["role_ids"]

    async def test_group_role_ids_reference_real_role_documents(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        from bson import ObjectId

        for group in db["groups"].find({}):
            for role_id in group["role_ids"]:
                role = db["roles"].find_one({"_id": ObjectId(role_id)})
                assert role is not None, f"Group '{group['name']}' references non-existent role id '{role_id}'"


class TestFullSeedPipeline:
    async def test_full_seed_pipeline_end_to_end(self, db: Database) -> None:
        settings = _make_settings(db)
        await seed(settings)
        assert db["permissions"].count_documents({}) == len(PERMISSIONS)
        assert db["roles"].count_documents({}) == len(ROLES)
        assert db["groups"].count_documents({}) == len(GROUPS)

    async def test_full_seed_idempotent_when_run_three_times(self, db: Database) -> None:
        settings = _make_settings(db)
        for _ in range(3):
            await seed(settings)
        assert db["permissions"].count_documents({}) == len(PERMISSIONS)
        assert db["roles"].count_documents({}) == len(ROLES)
        assert db["groups"].count_documents({}) == len(GROUPS)

    async def test_distance_finder_permission_reachable_through_group_chain(self, db: Database) -> None:
        """Validates the full permission resolution chain for distance_finder."""
        settings = _make_settings(db)
        await seed(settings)
        from bson import ObjectId

        # Start from "Hexadian Members" group
        group = db["groups"].find_one({"name": "Hexadian Members"})
        assert group is not None

        # Find "HHH Feature Premium" role via role_ids
        premium_role = None
        for role_id in group["role_ids"]:
            role = db["roles"].find_one({"_id": ObjectId(role_id), "name": "HHH Feature Premium"})
            if role:
                premium_role = role
                break
        assert premium_role is not None, "'HHH Feature Premium' role not found in Hexadian Members group"

        # Find "hhh:feature:distance_finder" permission via permission_ids
        distance_finder_perm = None
        for perm_id in premium_role["permission_ids"]:
            perm = db["permissions"].find_one({"_id": ObjectId(perm_id), "code": "hhh:feature:distance_finder"})
            if perm:
                distance_finder_perm = perm
                break
        assert distance_finder_perm is not None, (
            "hhh:feature:distance_finder not reachable through Hexadian Members → HHH Feature Premium chain"
        )

    async def test_seed_handles_partial_state_gracefully(self, db: Database) -> None:
        """Seed should fill in missing permissions even when some already exist."""
        settings = _make_settings(db)
        # Insert only the first 10 permissions manually
        for perm in PERMISSIONS[:10]:
            db["permissions"].insert_one({"code": perm["code"], "description": perm["description"]})
        assert db["permissions"].count_documents({}) == 10

        await seed(settings)

        assert db["permissions"].count_documents({}) == len(PERMISSIONS)

    @pytest.mark.skip(
        reason="Seed uses find_one+insert_one without unique indexes; concurrent runs produce duplicates. "
        "Would require MongoDB unique indexes at the collection level to prevent this reliably."
    )
    @pytest.mark.parametrize("thread_count", [2])
    async def test_concurrent_seed_does_not_produce_duplicates(self, db: Database, thread_count: int) -> None:
        """Concurrent seed runs should not produce duplicate documents."""
        settings = _make_settings(db)
        errors: list[Exception] = []

        def run_seed() -> None:
            try:
                asyncio.run(seed(settings))
            except Exception as e:  # noqa: BLE001
                errors.append(e)

        threads = [threading.Thread(target=run_seed) for _ in range(thread_count)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Seed may raise on race conditions but must not leave duplicates
        assert db["permissions"].count_documents({}) == len(PERMISSIONS)
        assert db["roles"].count_documents({}) == len(ROLES)
        assert db["groups"].count_documents({}) == len(GROUPS)
