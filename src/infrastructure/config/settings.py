from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "hexadian-auth-service"
    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db: str = "hexadian_auth"
    host: str = "0.0.0.0"
    port: int = 8006
    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_minutes: int = 60
    allowed_origins: list[str] = [
        "http://localhost:3000",  # H³ player frontend
        "http://localhost:3001",  # H³ backoffice frontend
        "http://localhost:3002",  # auth-backoffice
        "http://localhost:3003",  # auth-portal
    ]

    model_config = {"env_prefix": "HEXADIAN_AUTH_"}
