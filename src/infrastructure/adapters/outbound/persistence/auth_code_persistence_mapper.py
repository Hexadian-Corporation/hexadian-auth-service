from datetime import UTC

from src.domain.models.auth_code import AuthCode


class AuthCodePersistenceMapper:
    @staticmethod
    def to_document(auth_code: AuthCode) -> dict:
        return {
            "code": auth_code.code,
            "user_id": auth_code.user_id,
            "redirect_uri": auth_code.redirect_uri,
            "state": auth_code.state,
            "expires_at": auth_code.expires_at,
            "used": auth_code.used,
        }

    @staticmethod
    def to_domain(doc: dict) -> AuthCode:
        expires = doc["expires_at"]
        return AuthCode(
            id=str(doc["_id"]),
            code=doc.get("code", ""),
            user_id=doc.get("user_id", ""),
            redirect_uri=doc.get("redirect_uri", ""),
            state=doc.get("state", ""),
            expires_at=expires.replace(tzinfo=UTC) if expires.tzinfo is None else expires,
            used=doc.get("used", False),
        )
