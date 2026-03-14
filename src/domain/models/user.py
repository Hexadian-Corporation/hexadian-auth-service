from dataclasses import dataclass, field


@dataclass
class User:
    id: str | None = None
    username: str = ""
    email: str = ""
    hashed_password: str = ""
    roles: list[str] = field(default_factory=lambda: ["user"])
    is_active: bool = True
