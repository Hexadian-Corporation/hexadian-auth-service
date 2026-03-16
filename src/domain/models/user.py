from dataclasses import dataclass, field


@dataclass
class User:
    id: str | None = None
    username: str = ""
    hashed_password: str = ""
    roles: list[str] = field(default_factory=lambda: ["user"])
    is_active: bool = True
    rsi_handle: str = ""
    rsi_verified: bool = False
    rsi_verification_code: str | None = None
