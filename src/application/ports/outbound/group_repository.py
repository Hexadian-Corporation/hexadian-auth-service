from abc import ABC, abstractmethod

from src.domain.models.group import Group


class GroupRepository(ABC):
    @abstractmethod
    async def save(self, group: Group) -> Group: ...

    @abstractmethod
    async def find_by_id(self, group_id: str) -> Group | None: ...

    @abstractmethod
    async def find_by_name(self, name: str) -> Group | None: ...

    @abstractmethod
    async def find_all(self) -> list[Group]: ...

    @abstractmethod
    async def find_by_ids(self, group_ids: list[str]) -> list[Group]: ...

    @abstractmethod
    async def find_by_app_id(self, app_id: str) -> list[Group]: ...

    @abstractmethod
    async def delete(self, group_id: str) -> bool: ...
