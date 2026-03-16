from dataclasses import dataclass, field


@dataclass
class User:
    id: str | None = None
    username: str = ""
    hashed_password: str = ""
    group_ids: list[str] = field(default_factory=list)
    is_active: bool = True
    rsi_handle: str = ""
    rsi_verified: bool = False
    rsi_verification_code: str | None = None
