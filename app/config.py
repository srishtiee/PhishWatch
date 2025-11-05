from pydantic_settings import BaseSettings
from pydantic import AnyUrl


class Settings(BaseSettings):
    app_name: str = "PhishWatch API"
    env: str = "development"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Auth0
    auth0_domain: str
    auth0_audience: str
    auth0_algorithms: list[str] = ["RS256"]

    # Mongo
    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_db: str = "phishwatch"

    # Encryption key (base64-encoded 32 bytes for AES-GCM)
    encryption_key_b64: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

