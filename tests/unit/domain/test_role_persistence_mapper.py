from src.domain.models.role import Role
from src.infrastructure.adapters.outbound.persistence.role_persistence_mapper import RolePersistenceMapper


class TestRolePersistenceMapper:
    def test_to_document(self) -> None:
        role = Role(id="role-1", name="Content Manager", description="Manages content", permission_ids=["p1", "p2"])
        doc = RolePersistenceMapper.to_document(role)

        assert doc == {"name": "Content Manager", "description": "Manages content", "permission_ids": ["p1", "p2"]}
        assert "_id" not in doc

    def test_to_domain(self) -> None:
        doc = {"_id": "abc123", "name": "Content Manager", "description": "Manages content", "permission_ids": ["p1"]}
        role = RolePersistenceMapper.to_domain(doc)

        assert role.id == "abc123"
        assert role.name == "Content Manager"
        assert role.description == "Manages content"
        assert role.permission_ids == ["p1"]

    def test_to_domain_missing_fields_defaults(self) -> None:
        doc = {"_id": "abc123"}
        role = RolePersistenceMapper.to_domain(doc)

        assert role.id == "abc123"
        assert role.name == ""
        assert role.description == ""
        assert role.permission_ids == []
