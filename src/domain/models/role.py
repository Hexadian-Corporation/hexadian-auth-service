from dataclasses import dataclass, field


@dataclass
class Role:
    id: str | None = None
    name: str = ""
    description: str = ""
    permission_ids: list[str] = field(default_factory=list)
