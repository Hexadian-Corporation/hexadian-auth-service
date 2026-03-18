from src.application.ports.inbound.portal_settings_service import PortalSettingsService
from src.application.ports.outbound.portal_settings_repository import PortalSettingsRepository
from src.domain.models.portal_settings import PortalSettings


class PortalSettingsServiceImpl(PortalSettingsService):
    def __init__(self, portal_settings_repository: PortalSettingsRepository) -> None:
        self._portal_settings_repository = portal_settings_repository

    def get_settings(self) -> PortalSettings:
        settings = self._portal_settings_repository.get()
        if settings is None:
            settings = self._portal_settings_repository.save(PortalSettings())
        return settings

    def update_settings(self, default_redirect_url: str) -> PortalSettings:
        settings = self._portal_settings_repository.get()
        if settings is None:
            settings = PortalSettings()
        settings.default_redirect_url = default_redirect_url
        return self._portal_settings_repository.save(settings)
