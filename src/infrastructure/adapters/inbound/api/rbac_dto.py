from pydantic import BaseModel, Field


class PermissionCreateDTO(BaseModel):
    code: str
    description: str


class PermissionDTO(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    code: str
    description: str

    model_config = {"populate_by_name": True}


class RoleCreateDTO(BaseModel):
    name: str
    description: str
    permission_ids: list[str] = Field(default_factory=list)


class RoleDTO(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    name: str
    description: str
    permission_ids: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class GroupCreateDTO(BaseModel):
    name: str
    description: str
    role_ids: list[str] = Field(default_factory=list)


class GroupDTO(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    name: str
    description: str
    role_ids: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}


class UserGroupAssignDTO(BaseModel):
    group_id: str


class ResolvedPermissionsDTO(BaseModel):
    user_id: str
    permissions: list[str]
