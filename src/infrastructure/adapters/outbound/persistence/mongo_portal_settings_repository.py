from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from src.application.ports.outbound.portal_settings_repository import PortalSettingsRepository
from src.domain.models.portal_settings import PortalSettings
from src.infrastructure.adapters.outbound.persistence.portal_settings_persistence_mapper import (
    PortalSettingsPersistenceMapper,
)


class MongoPortalSettingsRepository(PortalSettingsRepository):
    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def get(self) -> PortalSettings | None:
        doc = await self._collection.find_one()
        if doc is None:
            return None
        return PortalSettingsPersistenceMapper.to_domain(doc)

    async def save(self, settings: PortalSettings) -> PortalSettings:
        doc = PortalSettingsPersistenceMapper.to_document(settings)
        if settings.id:
            await self._collection.replace_one({"_id": ObjectId(settings.id)}, doc, upsert=True)
            return settings
        result = await self._collection.insert_one(doc)
        settings.id = str(result.inserted_id)
        return settings
