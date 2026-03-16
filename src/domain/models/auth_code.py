from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta


@dataclass
class AuthCode:
    id: str | None = None
    code: str = ""
    user_id: str = ""
    redirect_uri: str = ""
    state: str = ""
    expires_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC) + timedelta(seconds=60))
    used: bool = False
