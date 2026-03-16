from src.application.ports.inbound.rbac_service import RbacService
from src.application.ports.outbound.group_repository import GroupRepository
from src.application.ports.outbound.permission_repository import PermissionRepository
from src.application.ports.outbound.role_repository import RoleRepository
from src.application.ports.outbound.user_repository import UserRepository
from src.domain.exceptions.group_exceptions import GroupNotFoundError
from src.domain.exceptions.permission_exceptions import PermissionNotFoundError
from src.domain.exceptions.role_exceptions import RoleNotFoundError
from src.domain.exceptions.user_exceptions import UserNotFoundError
from src.domain.models.group import Group
from src.domain.models.permission import Permission
from src.domain.models.role import Role


class RbacServiceImpl(RbacService):
    def __init__(
        self,
        user_repository: UserRepository,
        permission_repository: PermissionRepository,
        role_repository: RoleRepository,
        group_repository: GroupRepository,
    ) -> None:
        self._user_repository = user_repository
        self._permission_repository = permission_repository
        self._role_repository = role_repository
        self._group_repository = group_repository

    # -- Permission CRUD --

    def create_permission(self, code: str, description: str) -> Permission:
        permission = Permission(code=code, description=description)
        return self._permission_repository.save(permission)

    def get_permission(self, permission_id: str) -> Permission:
        permission = self._permission_repository.find_by_id(permission_id)
        if permission is None:
            raise PermissionNotFoundError(permission_id)
        return permission

    def list_permissions(self) -> list[Permission]:
        return self._permission_repository.find_all()

    def update_permission(self, permission_id: str, code: str, description: str) -> Permission:
        permission = self._permission_repository.find_by_id(permission_id)
        if permission is None:
            raise PermissionNotFoundError(permission_id)
        permission.code = code
        permission.description = description
        return self._permission_repository.save(permission)

    def delete_permission(self, permission_id: str) -> None:
        if not self._permission_repository.delete(permission_id):
            raise PermissionNotFoundError(permission_id)

    # -- Role CRUD --

    def create_role(self, name: str, description: str, permission_ids: list[str]) -> Role:
        role = Role(name=name, description=description, permission_ids=permission_ids)
        return self._role_repository.save(role)

    def get_role(self, role_id: str) -> Role:
        role = self._role_repository.find_by_id(role_id)
        if role is None:
            raise RoleNotFoundError(role_id)
        return role

    def list_roles(self) -> list[Role]:
        return self._role_repository.find_all()

    def update_role(self, role_id: str, name: str, description: str, permission_ids: list[str]) -> Role:
        role = self._role_repository.find_by_id(role_id)
        if role is None:
            raise RoleNotFoundError(role_id)
        role.name = name
        role.description = description
        role.permission_ids = permission_ids
        return self._role_repository.save(role)

    def delete_role(self, role_id: str) -> None:
        if not self._role_repository.delete(role_id):
            raise RoleNotFoundError(role_id)

    # -- Group CRUD --

    def create_group(self, name: str, description: str, role_ids: list[str]) -> Group:
        group = Group(name=name, description=description, role_ids=role_ids)
        return self._group_repository.save(group)

    def get_group(self, group_id: str) -> Group:
        group = self._group_repository.find_by_id(group_id)
        if group is None:
            raise GroupNotFoundError(group_id)
        return group

    def list_groups(self) -> list[Group]:
        return self._group_repository.find_all()

    def update_group(self, group_id: str, name: str, description: str, role_ids: list[str]) -> Group:
        group = self._group_repository.find_by_id(group_id)
        if group is None:
            raise GroupNotFoundError(group_id)
        group.name = name
        group.description = description
        group.role_ids = role_ids
        return self._group_repository.save(group)

    def delete_group(self, group_id: str) -> None:
        if not self._group_repository.delete(group_id):
            raise GroupNotFoundError(group_id)

    # -- Permission resolution --

    def resolve_permissions(self, user_id: str) -> list[str]:
        user = self._user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        if not user.group_ids:
            return []

        groups = self._group_repository.find_by_ids(user.group_ids)

        all_role_ids: list[str] = []
        for group in groups:
            all_role_ids.extend(group.role_ids)
        if not all_role_ids:
            return []

        roles = self._role_repository.find_by_ids(all_role_ids)

        all_permission_ids: list[str] = []
        for role in roles:
            all_permission_ids.extend(role.permission_ids)
        if not all_permission_ids:
            return []

        permissions = self._permission_repository.find_by_ids(all_permission_ids)

        seen: set[str] = set()
        codes: list[str] = []
        for p in permissions:
            if p.code not in seen:
                seen.add(p.code)
                codes.append(p.code)
        return codes

    # -- User-Group assignment --

    def assign_user_to_group(self, user_id: str, group_id: str) -> None:
        user = self._user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        group = self._group_repository.find_by_id(group_id)
        if group is None:
            raise GroupNotFoundError(group_id)

        if group_id not in user.group_ids:
            user.group_ids.append(group_id)
            self._user_repository.save(user)

    def remove_user_from_group(self, user_id: str, group_id: str) -> None:
        user = self._user_repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        if group_id in user.group_ids:
            user.group_ids.remove(group_id)
            self._user_repository.save(user)
