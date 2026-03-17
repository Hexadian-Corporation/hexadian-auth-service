from dataclasses import dataclass, field


@dataclass
class IntrospectionResult:
    active: bool = False
    sub: str | None = None
    username: str | None = None
    groups: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
    rsi_handle: str | None = None
    rsi_verified: bool | None = None
    exp: int | None = None
    iat: int | None = None
    is_user_active: bool | None = None
    reason: str | None = None
