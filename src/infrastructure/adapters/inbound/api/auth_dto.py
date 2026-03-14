from pydantic import BaseModel, Field


class UserDTO(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    username: str
    email: str
    roles: list[str] = Field(default_factory=lambda: ["user"])
    is_active: bool = True

    model_config = {"populate_by_name": True}


class RegisterDTO(BaseModel):
    username: str
    email: str
    password: str


class LoginDTO(BaseModel):
    username: str
    password: str


class TokenDTO(BaseModel):
    access_token: str
    token_type: str = "bearer"
