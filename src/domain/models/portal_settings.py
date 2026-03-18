from dataclasses import dataclass


@dataclass
class PortalSettings:
    id: str | None = None
    default_redirect_url: str = "https://www.hexadian.com"
