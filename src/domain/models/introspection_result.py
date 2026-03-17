from dataclasses import dataclass


@dataclass
class IntrospectionResult:
    active: bool = False
    sub: str | None = None
    username: str | None = None
    groups: list[str] | None = None
    roles: list[str] | None = None
    permissions: list[str] | None = None
    rsi_handle: str | None = None
    rsi_verified: bool | None = None
    exp: int | None = None
    iat: int | None = None
    is_user_active: bool | None = None
    reason: str | None = None
