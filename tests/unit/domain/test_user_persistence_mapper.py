from src.domain.models.user import User
from src.infrastructure.adapters.outbound.persistence.user_persistence_mapper import UserPersistenceMapper


class TestUserPersistenceMapperRsiFields:
    def test_to_document_includes_rsi_fields(self) -> None:
        user = User(
            id="user-1",
            username="test",
            hashed_password="salt:hash",
            rsi_handle="TestPilot",
            rsi_verified=True,
            rsi_verification_code="abc123",
        )
        doc = UserPersistenceMapper.to_document(user)

        assert doc["rsi_handle"] == "TestPilot"
        assert doc["rsi_verified"] is True
        assert doc["rsi_verification_code"] == "abc123"

    def test_to_document_rsi_fields_default(self) -> None:
        user = User(id="user-1", username="test")
        doc = UserPersistenceMapper.to_document(user)

        assert doc["rsi_handle"] == ""
        assert doc["rsi_verified"] is False
        assert doc["rsi_verification_code"] is None

    def test_to_domain_includes_rsi_fields(self) -> None:
        doc = {
            "_id": "abc123",
            "username": "test",
            "hashed_password": "salt:hash",
            "group_ids": [],
            "is_active": True,
            "rsi_handle": "TestPilot",
            "rsi_verified": True,
            "rsi_verification_code": "code123",
        }
        user = UserPersistenceMapper.to_domain(doc)

        assert user.rsi_handle == "TestPilot"
        assert user.rsi_verified is True
        assert user.rsi_verification_code == "code123"

    def test_to_domain_missing_rsi_fields_defaults(self) -> None:
        doc = {
            "_id": "abc123",
            "username": "test",
        }
        user = UserPersistenceMapper.to_domain(doc)

        assert user.rsi_handle == ""
        assert user.rsi_verified is False
        assert user.rsi_verification_code is None

    def test_to_document_excludes_email(self) -> None:
        user = User(id="user-1", username="test", rsi_handle="Pilot")
        doc = UserPersistenceMapper.to_document(user)

        assert "email" not in doc

    def test_to_domain_does_not_set_email(self) -> None:
        doc = {
            "_id": "abc123",
            "username": "test",
            "rsi_handle": "Pilot",
        }
        user = UserPersistenceMapper.to_domain(doc)

        assert not hasattr(user, "email")


class TestUserPersistenceMapperGroupIds:
    def test_to_document_includes_group_ids(self) -> None:
        user = User(id="user-1", username="test", group_ids=["grp-1", "grp-2"])
        doc = UserPersistenceMapper.to_document(user)

        assert doc["group_ids"] == ["grp-1", "grp-2"]

    def test_to_document_group_ids_default(self) -> None:
        user = User(id="user-1", username="test")
        doc = UserPersistenceMapper.to_document(user)

        assert doc["group_ids"] == []

    def test_to_document_excludes_roles(self) -> None:
        user = User(id="user-1", username="test")
        doc = UserPersistenceMapper.to_document(user)

        assert "roles" not in doc

    def test_to_domain_includes_group_ids(self) -> None:
        doc = {
            "_id": "abc123",
            "username": "test",
            "group_ids": ["grp-1", "grp-2"],
        }
        user = UserPersistenceMapper.to_domain(doc)

        assert user.group_ids == ["grp-1", "grp-2"]

    def test_to_domain_missing_group_ids_defaults(self) -> None:
        doc = {
            "_id": "abc123",
            "username": "test",
        }
        user = UserPersistenceMapper.to_domain(doc)

        assert user.group_ids == []
