from datetime import UTC, datetime

from bson import ObjectId

from src.domain.models.refresh_token import RefreshToken
from src.infrastructure.adapters.outbound.persistence.refresh_token_persistence_mapper import (
    RefreshTokenPersistenceMapper,
)


class TestRefreshTokenPersistenceMapper:
    def test_to_document_includes_all_fields(self) -> None:
        expires = datetime(2026, 3, 23, 12, 0, 0, tzinfo=UTC)
        token = RefreshToken(
            id="some-id",
            user_id="user-1",
            token="uuid-token",
            expires_at=expires,
            revoked=False,
        )

        doc = RefreshTokenPersistenceMapper.to_document(token)

        assert doc["user_id"] == "user-1"
        assert doc["token"] == "uuid-token"
        assert doc["expires_at"] == expires
        assert doc["revoked"] is False
        assert "_id" not in doc

    def test_to_document_excludes_id(self) -> None:
        token = RefreshToken(id="some-id", user_id="u1", token="t1")

        doc = RefreshTokenPersistenceMapper.to_document(token)

        assert "id" not in doc
        assert "_id" not in doc

    def test_to_domain_maps_all_fields(self) -> None:
        expires = datetime(2026, 3, 23, 12, 0, 0, tzinfo=UTC)
        doc = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "user_id": "user-1",
            "token": "uuid-token",
            "expires_at": expires,
            "revoked": True,
        }

        result = RefreshTokenPersistenceMapper.to_domain(doc)

        assert result.id == "507f1f77bcf86cd799439011"
        assert result.user_id == "user-1"
        assert result.token == "uuid-token"
        assert result.expires_at == expires
        assert result.revoked is True

    def test_to_domain_defaults_for_missing_fields(self) -> None:
        doc = {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "expires_at": datetime(2026, 3, 23, tzinfo=UTC),
        }

        result = RefreshTokenPersistenceMapper.to_domain(doc)

        assert result.user_id == ""
        assert result.token == ""
        assert result.revoked is False
