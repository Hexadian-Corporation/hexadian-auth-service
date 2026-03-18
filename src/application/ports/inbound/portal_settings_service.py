from abc import ABC, abstractmethod

from src.domain.models.portal_settings import PortalSettings


class PortalSettingsService(ABC):
    @abstractmethod
    def get_settings(self) -> PortalSettings: ...

    @abstractmethod
    def update_settings(self, default_redirect_url: str) -> PortalSettings: ...
