from src.domain.models.permission import Permission


class PermissionPersistenceMapper:
    @staticmethod
    def to_document(permission: Permission) -> dict:
        return {
            "code": permission.code,
            "description": permission.description,
        }

    @staticmethod
    def to_domain(doc: dict) -> Permission:
        return Permission(
            id=str(doc["_id"]),
            code=doc.get("code", ""),
            description=doc.get("description", ""),
        )
