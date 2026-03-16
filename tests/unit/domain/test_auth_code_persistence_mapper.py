from datetime import UTC, datetime

from bson import ObjectId

from src.infrastructure.adapters.outbound.persistence.auth_code_persistence_mapper import AuthCodePersistenceMapper


class TestAuthCodePersistenceMapper:
    def test_to_document_includes_all_fields(self) -> None:
        from src.domain.models.auth_code import AuthCode

        expires = datetime(2026, 1, 1, tzinfo=UTC)
        auth_code = AuthCode(
            id="ignored",
            code="test-code",
            user_id="user-1",
            redirect_uri="http://localhost:3000/callback",
            state="state123",
            expires_at=expires,
            used=False,
        )

        doc = AuthCodePersistenceMapper.to_document(auth_code)

        assert doc["code"] == "test-code"
        assert doc["user_id"] == "user-1"
        assert doc["redirect_uri"] == "http://localhost:3000/callback"
        assert doc["state"] == "state123"
        assert doc["expires_at"] == expires
        assert doc["used"] is False

    def test_to_document_excludes_id(self) -> None:
        from src.domain.models.auth_code import AuthCode

        auth_code = AuthCode(id="should-not-appear", code="test-code")

        doc = AuthCodePersistenceMapper.to_document(auth_code)

        assert "_id" not in doc
        assert "id" not in doc

    def test_to_domain_maps_all_fields(self) -> None:
        expires = datetime(2026, 1, 1, tzinfo=UTC)
        doc = {
            "_id": ObjectId(),
            "code": "test-code",
            "user_id": "user-1",
            "redirect_uri": "http://localhost:3000/callback",
            "state": "state123",
            "expires_at": expires,
            "used": True,
        }

        auth_code = AuthCodePersistenceMapper.to_domain(doc)

        assert auth_code.id == str(doc["_id"])
        assert auth_code.code == "test-code"
        assert auth_code.user_id == "user-1"
        assert auth_code.redirect_uri == "http://localhost:3000/callback"
        assert auth_code.state == "state123"
        assert auth_code.expires_at == expires
        assert auth_code.used is True

    def test_to_domain_defaults_for_missing_fields(self) -> None:
        doc = {
            "_id": ObjectId(),
            "expires_at": datetime(2026, 1, 1, tzinfo=UTC),
        }

        auth_code = AuthCodePersistenceMapper.to_domain(doc)

        assert auth_code.code == ""
        assert auth_code.user_id == ""
        assert auth_code.redirect_uri == ""
        assert auth_code.state == ""
        assert auth_code.used is False
