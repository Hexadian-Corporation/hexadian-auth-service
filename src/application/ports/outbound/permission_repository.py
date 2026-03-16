from abc import ABC, abstractmethod

from src.domain.models.permission import Permission


class PermissionRepository(ABC):
    @abstractmethod
    def save(self, permission: Permission) -> Permission: ...

    @abstractmethod
    def find_by_id(self, permission_id: str) -> Permission | None: ...

    @abstractmethod
    def find_by_code(self, code: str) -> Permission | None: ...

    @abstractmethod
    def find_all(self) -> list[Permission]: ...

    @abstractmethod
    def find_by_ids(self, permission_ids: list[str]) -> list[Permission]: ...

    @abstractmethod
    def delete(self, permission_id: str) -> bool: ...
