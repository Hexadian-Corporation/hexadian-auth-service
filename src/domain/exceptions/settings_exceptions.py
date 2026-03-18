class SettingsNotFoundError(Exception):
    def __init__(self) -> None:
        super().__init__("Portal settings not found")
