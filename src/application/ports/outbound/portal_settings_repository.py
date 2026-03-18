from abc import ABC, abstractmethod

from src.domain.models.portal_settings import PortalSettings


class PortalSettingsRepository(ABC):
    @abstractmethod
    def get(self) -> PortalSettings | None: ...

    @abstractmethod
    def save(self, settings: PortalSettings) -> PortalSettings: ...
