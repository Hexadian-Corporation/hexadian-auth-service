from bson import ObjectId
from pymongo.collection import Collection

from src.application.ports.outbound.portal_settings_repository import PortalSettingsRepository
from src.domain.models.portal_settings import PortalSettings
from src.infrastructure.adapters.outbound.persistence.portal_settings_persistence_mapper import (
    PortalSettingsPersistenceMapper,
)


class MongoPortalSettingsRepository(PortalSettingsRepository):
    def __init__(self, collection: Collection) -> None:
        self._collection = collection

    def get(self) -> PortalSettings | None:
        doc = self._collection.find_one()
        if doc is None:
            return None
        return PortalSettingsPersistenceMapper.to_domain(doc)

    def save(self, settings: PortalSettings) -> PortalSettings:
        doc = PortalSettingsPersistenceMapper.to_document(settings)
        if settings.id:
            self._collection.replace_one({"_id": ObjectId(settings.id)}, doc, upsert=True)
            return settings
        result = self._collection.insert_one(doc)
        settings.id = str(result.inserted_id)
        return settings
