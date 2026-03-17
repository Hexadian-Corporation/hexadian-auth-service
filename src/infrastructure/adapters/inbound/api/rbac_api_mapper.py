from src.domain.models.group import Group
from src.domain.models.permission import Permission
from src.domain.models.role import Role
from src.infrastructure.adapters.inbound.api.rbac_dto import (
    GroupDTO,
    PermissionDTO,
    RoleDTO,
)


class RbacApiMapper:
    @staticmethod
    def permission_to_dto(permission: Permission) -> PermissionDTO:
        return PermissionDTO(
            _id=permission.id,
            code=permission.code,
            description=permission.description,
        )

    @staticmethod
    def role_to_dto(role: Role) -> RoleDTO:
        return RoleDTO(
            _id=role.id,
            name=role.name,
            description=role.description,
            permission_ids=role.permission_ids,
        )

    @staticmethod
    def group_to_dto(group: Group) -> GroupDTO:
        return GroupDTO(
            _id=group.id,
            name=group.name,
            description=group.description,
            role_ids=group.role_ids,
            auto_assign_apps=group.auto_assign_apps,
        )
