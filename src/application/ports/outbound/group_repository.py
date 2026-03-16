from abc import ABC, abstractmethod

from src.domain.models.group import Group


class GroupRepository(ABC):
    @abstractmethod
    def save(self, group: Group) -> Group: ...

    @abstractmethod
    def find_by_id(self, group_id: str) -> Group | None: ...

    @abstractmethod
    def find_by_name(self, name: str) -> Group | None: ...

    @abstractmethod
    def find_all(self) -> list[Group]: ...

    @abstractmethod
    def find_by_ids(self, group_ids: list[str]) -> list[Group]: ...

    @abstractmethod
    def delete(self, group_id: str) -> bool: ...
