from dataclasses import dataclass, field


@dataclass
class Group:
    id: str | None = None
    name: str = ""
    description: str = ""
    role_ids: list[str] = field(default_factory=list)
    auto_assign_apps: list[str] = field(default_factory=list)
