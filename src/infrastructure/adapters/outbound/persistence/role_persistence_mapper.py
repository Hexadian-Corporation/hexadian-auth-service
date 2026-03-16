from src.domain.models.role import Role


class RolePersistenceMapper:
    @staticmethod
    def to_document(role: Role) -> dict:
        return {
            "name": role.name,
            "description": role.description,
            "permission_ids": role.permission_ids,
        }

    @staticmethod
    def to_domain(doc: dict) -> Role:
        return Role(
            id=str(doc["_id"]),
            name=doc.get("name", ""),
            description=doc.get("description", ""),
            permission_ids=doc.get("permission_ids", []),
        )
