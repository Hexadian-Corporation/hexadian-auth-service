from src.domain.models.user import User


class UserPersistenceMapper:

    @staticmethod
    def to_document(user: User) -> dict:
        return {
            "username": user.username,
            "email": user.email,
            "hashed_password": user.hashed_password,
            "roles": user.roles,
            "is_active": user.is_active,
        }

    @staticmethod
    def to_domain(doc: dict) -> User:
        return User(
            id=str(doc["_id"]),
            username=doc.get("username", ""),
            email=doc.get("email", ""),
            hashed_password=doc.get("hashed_password", ""),
            roles=doc.get("roles", ["user"]),
            is_active=doc.get("is_active", True),
        )
