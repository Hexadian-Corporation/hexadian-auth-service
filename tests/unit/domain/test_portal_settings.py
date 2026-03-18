from src.domain.models.portal_settings import PortalSettings


class TestPortalSettings:
    def test_default_values(self) -> None:
        settings = PortalSettings()

        assert settings.id is None
        assert settings.default_redirect_url == "https://www.hexadian.com"

    def test_custom_values(self) -> None:
        settings = PortalSettings(id="s-1", default_redirect_url="https://example.com")

        assert settings.id == "s-1"
        assert settings.default_redirect_url == "https://example.com"
