from src.domain.models.permission import Permission
from src.infrastructure.adapters.outbound.persistence.permission_persistence_mapper import PermissionPersistenceMapper


class TestPermissionPersistenceMapper:
    def test_to_document(self) -> None:
        permission = Permission(id="perm-1", code="hhh:contracts:read", description="View contracts")
        doc = PermissionPersistenceMapper.to_document(permission)

        assert doc == {"code": "hhh:contracts:read", "description": "View contracts"}
        assert "_id" not in doc

    def test_to_domain(self) -> None:
        doc = {"_id": "abc123", "code": "hhh:contracts:read", "description": "View contracts"}
        permission = PermissionPersistenceMapper.to_domain(doc)

        assert permission.id == "abc123"
        assert permission.code == "hhh:contracts:read"
        assert permission.description == "View contracts"

    def test_to_domain_missing_fields_defaults(self) -> None:
        doc = {"_id": "abc123"}
        permission = PermissionPersistenceMapper.to_domain(doc)

        assert permission.id == "abc123"
        assert permission.code == ""
        assert permission.description == ""
