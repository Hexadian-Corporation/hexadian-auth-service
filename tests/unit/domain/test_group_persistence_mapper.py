from src.domain.models.group import Group
from src.infrastructure.adapters.outbound.persistence.group_persistence_mapper import GroupPersistenceMapper


class TestGroupPersistenceMapper:
    def test_to_document(self) -> None:
        group = Group(id="grp-1", name="Admins", description="Admin group", role_ids=["r1", "r2"])
        doc = GroupPersistenceMapper.to_document(group)

        assert doc == {"name": "Admins", "description": "Admin group", "role_ids": ["r1", "r2"], "auto_assign_apps": []}
        assert "_id" not in doc

    def test_to_domain(self) -> None:
        doc = {"_id": "abc123", "name": "Admins", "description": "Admin group", "role_ids": ["r1"]}
        group = GroupPersistenceMapper.to_domain(doc)

        assert group.id == "abc123"
        assert group.name == "Admins"
        assert group.description == "Admin group"
        assert group.role_ids == ["r1"]
        assert group.auto_assign_apps == []

    def test_to_domain_missing_fields_defaults(self) -> None:
        doc = {"_id": "abc123"}
        group = GroupPersistenceMapper.to_domain(doc)

        assert group.id == "abc123"
        assert group.name == ""
        assert group.description == ""
        assert group.role_ids == []
        assert group.auto_assign_apps == []
