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


class VerificationResultDTO(BaseModel):
    verification_code: str | None = None
    verified: bool
    message: str
