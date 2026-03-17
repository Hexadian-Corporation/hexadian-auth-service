from pydantic import BaseModel, Field


class UserDTO(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    username: str
    group_ids: list[str] = Field(default_factory=list)
    is_active: bool = True
    rsi_handle: str = ""
    rsi_verified: bool = False

    model_config = {"populate_by_name": True}


class RegisterDTO(BaseModel):
    username: str
    password: str
    rsi_handle: str = Field(pattern=r"^[A-Za-z0-9_-]{3,30}$")


class LoginDTO(BaseModel):
    username: str
    password: str


class TokenDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenDTO(BaseModel):
    refresh_token: str


class StartVerificationDTO(BaseModel):
    rsi_handle: str = Field(pattern=r"^[A-Za-z0-9_-]{3,30}$")


class UserUpdateDTO(BaseModel):
    username: str | None = None
    rsi_handle: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{3,30}$")


class VerificationResultDTO(BaseModel):
    verification_code: str | None = None
    verified: bool
    message: str


class AuthorizeDTO(BaseModel):
    username: str
    password: str
    redirect_uri: str
    state: str = ""


class AuthorizeResponseDTO(BaseModel):
    code: str
    state: str
    redirect_uri: str


class TokenExchangeDTO(BaseModel):
    code: str
    redirect_uri: str


class PasswordChangeDTO(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)


class PasswordResetDTO(BaseModel):
    new_password: str = Field(min_length=8)


class TokenIntrospectRequestDTO(BaseModel):
    token: str


class TokenIntrospectResponseDTO(BaseModel):
    active: bool
    sub: str | None = None
    username: str | None = None
    groups: list[str] | None = None
    roles: list[str] | None = None
    permissions: list[str] | None = None
    rsi_handle: str | None = None
    rsi_verified: bool | None = None
    exp: int | None = None
    iat: int | None = None
    is_user_active: bool | None = None
    reason: str | None = None
