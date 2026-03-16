from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from hexadian_auth_common.context import UserContext
from hexadian_auth_common.fastapi import _stub_jwt_auth, require_permission

from src.application.ports.inbound.rbac_service import RbacService
from src.domain.exceptions.group_exceptions import GroupNotFoundError
from src.domain.exceptions.permission_exceptions import PermissionNotFoundError
from src.domain.exceptions.role_exceptions import RoleNotFoundError
from src.domain.exceptions.user_exceptions import UserNotFoundError
from src.infrastructure.adapters.inbound.api.rbac_api_mapper import RbacApiMapper
from src.infrastructure.adapters.inbound.api.rbac_dto import (
    GroupCreateDTO,
    GroupDTO,
    PermissionCreateDTO,
    PermissionDTO,
    ResolvedPermissionsDTO,
    RoleCreateDTO,
    RoleDTO,
    UserGroupAssignDTO,
)

rbac_router = APIRouter(prefix="/rbac", tags=["rbac"])

_rbac_service: RbacService | None = None


def init_rbac_router(rbac_service: RbacService) -> None:
    global _rbac_service
    _rbac_service = rbac_service


# ---------------------------------------------------------------------------
# Permission CRUD
# ---------------------------------------------------------------------------


@rbac_router.post(
    "/permissions",
    response_model=PermissionDTO,
    status_code=201,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def create_permission(dto: PermissionCreateDTO) -> PermissionDTO:
    permission = _rbac_service.create_permission(dto.code, dto.description)
    return RbacApiMapper.permission_to_dto(permission)


@rbac_router.get(
    "/permissions",
    response_model=list[PermissionDTO],
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def list_permissions() -> list[PermissionDTO]:
    return [RbacApiMapper.permission_to_dto(p) for p in _rbac_service.list_permissions()]


@rbac_router.get(
    "/permissions/{permission_id}",
    response_model=PermissionDTO,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def get_permission(permission_id: str) -> PermissionDTO:
    try:
        permission = _rbac_service.get_permission(permission_id)
    except PermissionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RbacApiMapper.permission_to_dto(permission)


@rbac_router.put(
    "/permissions/{permission_id}",
    response_model=PermissionDTO,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def update_permission(permission_id: str, dto: PermissionCreateDTO) -> PermissionDTO:
    try:
        permission = _rbac_service.update_permission(permission_id, dto.code, dto.description)
    except PermissionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RbacApiMapper.permission_to_dto(permission)


@rbac_router.delete(
    "/permissions/{permission_id}",
    status_code=204,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def delete_permission(permission_id: str) -> None:
    try:
        _rbac_service.delete_permission(permission_id)
    except PermissionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Role CRUD
# ---------------------------------------------------------------------------


@rbac_router.post(
    "/roles",
    response_model=RoleDTO,
    status_code=201,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def create_role(dto: RoleCreateDTO) -> RoleDTO:
    role = _rbac_service.create_role(dto.name, dto.description, dto.permission_ids)
    return RbacApiMapper.role_to_dto(role)


@rbac_router.get(
    "/roles",
    response_model=list[RoleDTO],
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def list_roles() -> list[RoleDTO]:
    return [RbacApiMapper.role_to_dto(r) for r in _rbac_service.list_roles()]


@rbac_router.get(
    "/roles/{role_id}",
    response_model=RoleDTO,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def get_role(role_id: str) -> RoleDTO:
    try:
        role = _rbac_service.get_role(role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RbacApiMapper.role_to_dto(role)


@rbac_router.put(
    "/roles/{role_id}",
    response_model=RoleDTO,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def update_role(role_id: str, dto: RoleCreateDTO) -> RoleDTO:
    try:
        role = _rbac_service.update_role(role_id, dto.name, dto.description, dto.permission_ids)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RbacApiMapper.role_to_dto(role)


@rbac_router.delete(
    "/roles/{role_id}",
    status_code=204,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def delete_role(role_id: str) -> None:
    try:
        _rbac_service.delete_role(role_id)
    except RoleNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Group CRUD
# ---------------------------------------------------------------------------


@rbac_router.post(
    "/groups",
    response_model=GroupDTO,
    status_code=201,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def create_group(dto: GroupCreateDTO) -> GroupDTO:
    group = _rbac_service.create_group(dto.name, dto.description, dto.role_ids)
    return RbacApiMapper.group_to_dto(group)


@rbac_router.get(
    "/groups",
    response_model=list[GroupDTO],
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def list_groups() -> list[GroupDTO]:
    return [RbacApiMapper.group_to_dto(g) for g in _rbac_service.list_groups()]


@rbac_router.get(
    "/groups/{group_id}",
    response_model=GroupDTO,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def get_group(group_id: str) -> GroupDTO:
    try:
        group = _rbac_service.get_group(group_id)
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RbacApiMapper.group_to_dto(group)


@rbac_router.put(
    "/groups/{group_id}",
    response_model=GroupDTO,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def update_group(group_id: str, dto: GroupCreateDTO) -> GroupDTO:
    try:
        group = _rbac_service.update_group(group_id, dto.name, dto.description, dto.role_ids)
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return RbacApiMapper.group_to_dto(group)


@rbac_router.delete(
    "/groups/{group_id}",
    status_code=204,
    dependencies=[Depends(require_permission("rbac:manage"))],
)
def delete_group(group_id: str) -> None:
    try:
        _rbac_service.delete_group(group_id)
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# User-Group assignment
# ---------------------------------------------------------------------------


@rbac_router.post(
    "/users/{user_id}/groups",
    status_code=204,
    dependencies=[Depends(require_permission("users:admin"))],
)
def assign_user_to_group(user_id: str, dto: UserGroupAssignDTO) -> None:
    try:
        _rbac_service.assign_user_to_group(user_id, dto.group_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except GroupNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@rbac_router.delete(
    "/users/{user_id}/groups/{group_id}",
    status_code=204,
    dependencies=[Depends(require_permission("users:admin"))],
)
def remove_user_from_group(user_id: str, group_id: str) -> None:
    try:
        _rbac_service.remove_user_from_group(user_id, group_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


# ---------------------------------------------------------------------------
# Resolved permissions
# ---------------------------------------------------------------------------


@rbac_router.get(
    "/users/{user_id}/permissions",
    response_model=ResolvedPermissionsDTO,
)
def get_resolved_permissions(
    user_id: str,
    user_ctx: Annotated[UserContext, Depends(_stub_jwt_auth)],
) -> ResolvedPermissionsDTO:
    if user_ctx.user_id != user_id and "users:read" not in user_ctx.permissions:
        raise HTTPException(status_code=403, detail="Missing required permission: users:read")
    try:
        codes = _rbac_service.resolve_permissions(user_id)
    except UserNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ResolvedPermissionsDTO(user_id=user_id, permissions=codes)
