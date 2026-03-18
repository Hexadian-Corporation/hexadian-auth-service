from pydantic import BaseModel, Field


class PortalSettingsDTO(BaseModel):
    id: str | None = Field(default=None, alias="_id")
    default_redirect_url: str

    model_config = {"populate_by_name": True}


class PortalSettingsUpdateDTO(BaseModel):
    default_redirect_url: str


class PortalRedirectDTO(BaseModel):
    default_redirect_url: str
