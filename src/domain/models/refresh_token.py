from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class RefreshToken:
    id: str | None = None
    user_id: str = ""
    token: str = ""
    expires_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    revoked: bool = False
