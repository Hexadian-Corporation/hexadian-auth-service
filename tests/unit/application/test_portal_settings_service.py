from unittest.mock import MagicMock

import pytest

from src.application.ports.outbound.portal_settings_repository import PortalSettingsRepository
from src.application.services.portal_settings_service_impl import PortalSettingsServiceImpl
from src.domain.models.portal_settings import PortalSettings


@pytest.fixture()
def mock_repository() -> MagicMock:
    return MagicMock(spec=PortalSettingsRepository)


@pytest.fixture()
def service(mock_repository: MagicMock) -> PortalSettingsServiceImpl:
    return PortalSettingsServiceImpl(portal_settings_repository=mock_repository)


class TestGetSettings:
    def test_returns_existing_settings(self, service: PortalSettingsServiceImpl, mock_repository: MagicMock) -> None:
        existing = PortalSettings(id="s-1", default_redirect_url="https://example.com")
        mock_repository.get.return_value = existing

        result = service.get_settings()

        assert result.id == "s-1"
        assert result.default_redirect_url == "https://example.com"
        mock_repository.save.assert_not_called()

    def test_creates_default_when_none_exists(
        self, service: PortalSettingsServiceImpl, mock_repository: MagicMock
    ) -> None:
        mock_repository.get.return_value = None
        mock_repository.save.side_effect = lambda s: PortalSettings(
            id="s-new", default_redirect_url=s.default_redirect_url
        )

        result = service.get_settings()

        assert result.id == "s-new"
        assert result.default_redirect_url == "https://www.hexadian.com"
        mock_repository.save.assert_called_once()


class TestUpdateSettings:
    def test_updates_existing_settings(self, service: PortalSettingsServiceImpl, mock_repository: MagicMock) -> None:
        existing = PortalSettings(id="s-1", default_redirect_url="https://old.com")
        mock_repository.get.return_value = existing
        mock_repository.save.side_effect = lambda s: s

        result = service.update_settings("https://new.com")

        assert result.default_redirect_url == "https://new.com"
        assert result.id == "s-1"
        mock_repository.save.assert_called_once()

    def test_creates_and_updates_when_none_exists(
        self, service: PortalSettingsServiceImpl, mock_repository: MagicMock
    ) -> None:
        mock_repository.get.return_value = None
        mock_repository.save.side_effect = lambda s: PortalSettings(
            id="s-new", default_redirect_url=s.default_redirect_url
        )

        result = service.update_settings("https://new.com")

        assert result.default_redirect_url == "https://new.com"
        mock_repository.save.assert_called_once()
