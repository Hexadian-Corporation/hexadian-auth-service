from src.domain.models.user import User


class UserPersistenceMapper:
    @staticmethod
    def to_document(user: User) -> dict:
        return {
            "username": user.username,
            "hashed_password": user.hashed_password,
            "group_ids": user.group_ids,
            "is_active": user.is_active,
            "rsi_handle": user.rsi_handle,
            "rsi_verified": user.rsi_verified,
            "rsi_verification_code": user.rsi_verification_code,
        }

    @staticmethod
    def to_domain(doc: dict) -> User:
        return User(
            id=str(doc["_id"]),
            username=doc.get("username", ""),
            hashed_password=doc.get("hashed_password", ""),
            group_ids=doc.get("group_ids", []),
            is_active=doc.get("is_active", True),
            rsi_handle=doc.get("rsi_handle", ""),
            rsi_verified=doc.get("rsi_verified", False),
            rsi_verification_code=doc.get("rsi_verification_code"),
        )
