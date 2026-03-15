from src.domain.models.user import User
from src.infrastructure.adapters.outbound.persistence.user_persistence_mapper import UserPersistenceMapper


class TestUserPersistenceMapperRsiFields:
    def test_to_document_includes_rsi_fields(self) -> None:
        user = User(
            id="user-1",
            username="test",
            email="test@example.com",
            hashed_password="salt:hash",
            rsi_handle="TestPilot",
            rsi_verified=True,
            rsi_verification_code="abc123",
        )
        doc = UserPersistenceMapper.to_document(user)

        assert doc["rsi_handle"] == "TestPilot"
        assert doc["rsi_verified"] is True
        assert doc["rsi_verification_code"] == "abc123"

    def test_to_document_rsi_fields_default_none(self) -> None:
        user = User(id="user-1", username="test", email="test@example.com")
        doc = UserPersistenceMapper.to_document(user)

        assert doc["rsi_handle"] is None
        assert doc["rsi_verified"] is False
        assert doc["rsi_verification_code"] is None

    def test_to_domain_includes_rsi_fields(self) -> None:
        doc = {
            "_id": "abc123",
            "username": "test",
            "email": "test@example.com",
            "hashed_password": "salt:hash",
            "roles": ["user"],
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
            "email": "test@example.com",
        }
        user = UserPersistenceMapper.to_domain(doc)

        assert user.rsi_handle is None
        assert user.rsi_verified is False
        assert user.rsi_verification_code is None
