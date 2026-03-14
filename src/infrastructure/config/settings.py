from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "hhh-auth-service"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "hhh_auth"
    host: str = "0.0.0.0"
    port: int = 8006
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60

    model_config = {"env_prefix": "HHH_AUTH_"}
