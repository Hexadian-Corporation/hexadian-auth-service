from abc import ABC, abstractmethod

from src.domain.models.portal_settings import PortalSettings


class PortalSettingsRepository(ABC):
    @abstractmethod
    async def get(self) -> PortalSettings | None: ...

    @abstractmethod
    async def save(self, settings: PortalSettings) -> PortalSettings: ...
