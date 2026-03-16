from abc import ABC, abstractmethod

from src.domain.models.group import Group
from src.domain.models.permission import Permission
from src.domain.models.role import Role


class RbacService(ABC):
    # -- Permission CRUD --
    @abstractmethod
    def create_permission(self, code: str, description: str) -> Permission: ...

    @abstractmethod
    def get_permission(self, permission_id: str) -> Permission: ...

    @abstractmethod
    def list_permissions(self) -> list[Permission]: ...

    @abstractmethod
    def update_permission(self, permission_id: str, code: str, description: str) -> Permission: ...

    @abstractmethod
    def delete_permission(self, permission_id: str) -> None: ...

    # -- Role CRUD --
    @abstractmethod
    def create_role(self, name: str, description: str, permission_ids: list[str]) -> Role: ...

    @abstractmethod
    def get_role(self, role_id: str) -> Role: ...

    @abstractmethod
    def list_roles(self) -> list[Role]: ...

    @abstractmethod
    def update_role(self, role_id: str, name: str, description: str, permission_ids: list[str]) -> Role: ...

    @abstractmethod
    def delete_role(self, role_id: str) -> None: ...

    # -- Group CRUD --
    @abstractmethod
    def create_group(self, name: str, description: str, role_ids: list[str]) -> Group: ...

    @abstractmethod
    def get_group(self, group_id: str) -> Group: ...

    @abstractmethod
    def list_groups(self) -> list[Group]: ...

    @abstractmethod
    def update_group(self, group_id: str, name: str, description: str, role_ids: list[str]) -> Group: ...

    @abstractmethod
    def delete_group(self, group_id: str) -> None: ...

    # -- Permission resolution --
    @abstractmethod
    def resolve_permissions(self, user_id: str) -> list[str]:
        """Resolve all permission codes for a user: User → Groups → Roles → Permissions."""
        ...

    # -- User-Group assignment --
    @abstractmethod
    def assign_user_to_group(self, user_id: str, group_id: str) -> None: ...

    @abstractmethod
    def remove_user_from_group(self, user_id: str, group_id: str) -> None: ...
