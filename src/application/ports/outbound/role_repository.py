from abc import ABC, abstractmethod

from src.domain.models.role import Role


class RoleRepository(ABC):
    @abstractmethod
    async def save(self, role: Role) -> Role: ...

    @abstractmethod
    async def find_by_id(self, role_id: str) -> Role | None: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> Role | None: ...

    @abstractmethod
    async def find_all(self) -> list[Role]: ...

    @abstractmethod
    async def find_by_ids(self, role_ids: list[str]) -> list[Role]: ...

    @abstractmethod
    async def delete(self, role_id: str) -> bool: ...
