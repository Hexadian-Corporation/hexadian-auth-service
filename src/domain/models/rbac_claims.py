from dataclasses import dataclass, field


@dataclass
class RbacClaims:
    groups: list[str] = field(default_factory=list)
    roles: list[str] = field(default_factory=list)
    permissions: list[str] = field(default_factory=list)
