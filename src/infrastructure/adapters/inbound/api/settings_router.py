from fastapi import APIRouter, Depends
from hexadian_auth_common.fastapi import require_permission

from src.application.ports.inbound.portal_settings_service import PortalSettingsService
from src.infrastructure.adapters.inbound.api.settings_dto import (
    PortalRedirectDTO,
    PortalSettingsDTO,
    PortalSettingsUpdateDTO,
)

settings_router = APIRouter(prefix="/settings", tags=["settings"])

_settings_service: PortalSettingsService | None = None

_manage = [Depends(require_permission("auth:settings:manage"))]


def init_settings_router(settings_service: PortalSettingsService) -> None:
    global _settings_service
    _settings_service = settings_service


@settings_router.get(
    "/portal",
    response_model=PortalRedirectDTO,
)
def get_portal_redirect() -> PortalRedirectDTO:
    settings = _settings_service.get_settings()
    return PortalRedirectDTO(default_redirect_url=settings.default_redirect_url)


@settings_router.get(
    "",
    response_model=PortalSettingsDTO,
    dependencies=_manage,
)
def get_settings() -> PortalSettingsDTO:
    settings = _settings_service.get_settings()
    return PortalSettingsDTO(_id=settings.id, default_redirect_url=settings.default_redirect_url)


@settings_router.put(
    "",
    response_model=PortalSettingsDTO,
    dependencies=_manage,
)
def update_settings(dto: PortalSettingsUpdateDTO) -> PortalSettingsDTO:
    settings = _settings_service.update_settings(dto.default_redirect_url)
    return PortalSettingsDTO(_id=settings.id, default_redirect_url=settings.default_redirect_url)
