from src.domain.exceptions.settings_exceptions import SettingsNotFoundError


class TestSettingsNotFoundError:
    def test_message(self) -> None:
        error = SettingsNotFoundError()
        assert "Portal settings not found" in str(error)
