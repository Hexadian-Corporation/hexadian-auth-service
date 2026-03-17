from datetime import UTC

from src.domain.models.refresh_token import RefreshToken


class RefreshTokenPersistenceMapper:
    @staticmethod
    def to_document(token: RefreshToken) -> dict:
        return {
            "user_id": token.user_id,
            "token": token.token,
            "expires_at": token.expires_at,
            "revoked": token.revoked,
        }

    @staticmethod
    def to_domain(doc: dict) -> RefreshToken:
        return RefreshToken(
            id=str(doc["_id"]),
            user_id=doc.get("user_id", ""),
            token=doc.get("token", ""),
            expires_at=doc["expires_at"].replace(tzinfo=UTC) if doc["expires_at"].tzinfo is None else doc["expires_at"],
            revoked=doc.get("revoked", False),
        )
