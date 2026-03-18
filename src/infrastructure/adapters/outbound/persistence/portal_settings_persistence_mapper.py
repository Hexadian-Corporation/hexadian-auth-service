from src.domain.models.portal_settings import PortalSettings


class PortalSettingsPersistenceMapper:
    @staticmethod
    def to_document(settings: PortalSettings) -> dict:
        return {
            "default_redirect_url": settings.default_redirect_url,
        }

    @staticmethod
    def to_domain(doc: dict) -> PortalSettings:
        return PortalSettings(
            id=str(doc["_id"]),
            default_redirect_url=doc.get("default_redirect_url", "https://www.hexadian.com"),
        )
