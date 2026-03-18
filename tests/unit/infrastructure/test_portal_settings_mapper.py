from bson import ObjectId

from src.domain.models.portal_settings import PortalSettings
from src.infrastructure.adapters.outbound.persistence.portal_settings_persistence_mapper import (
    PortalSettingsPersistenceMapper,
)


class TestPortalSettingsPersistenceMapper:
    def test_to_document(self) -> None:
        settings = PortalSettings(id="s-1", default_redirect_url="https://example.com")

        doc = PortalSettingsPersistenceMapper.to_document(settings)

        assert doc == {"default_redirect_url": "https://example.com"}
        assert "_id" not in doc

    def test_to_domain(self) -> None:
        oid = ObjectId()
        doc = {"_id": oid, "default_redirect_url": "https://example.com"}

        settings = PortalSettingsPersistenceMapper.to_domain(doc)

        assert settings.id == str(oid)
        assert settings.default_redirect_url == "https://example.com"

    def test_to_domain_uses_default_url_when_missing(self) -> None:
        oid = ObjectId()
        doc = {"_id": oid}

        settings = PortalSettingsPersistenceMapper.to_domain(doc)

        assert settings.default_redirect_url == "https://www.hexadian.com"
