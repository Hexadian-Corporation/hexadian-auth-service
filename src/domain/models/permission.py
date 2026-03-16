from dataclasses import dataclass


@dataclass
class Permission:
    id: str | None = None
    code: str = ""
    description: str = ""
