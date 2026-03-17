from src.domain.models.group import Group


class GroupPersistenceMapper:
    @staticmethod
    def to_document(group: Group) -> dict:
        return {
            "name": group.name,
            "description": group.description,
            "role_ids": group.role_ids,
            "auto_assign_apps": group.auto_assign_apps,
        }

    @staticmethod
    def to_domain(doc: dict) -> Group:
        return Group(
            id=str(doc["_id"]),
            name=doc.get("name", ""),
            description=doc.get("description", ""),
            role_ids=doc.get("role_ids", []),
            auto_assign_apps=doc.get("auto_assign_apps", []),
        )
