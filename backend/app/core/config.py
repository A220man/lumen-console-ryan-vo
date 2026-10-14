from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql+asyncpg://lumen:lumen@localhost:5432/lumen"

    # Encryption
    encryption_key: str = ""

    # GitHub
    github_app_id: str | None = None
    github_app_private_key: str | None = None
    github_token: str | None = None

    # OIDC
    oidc_issuer: str = "http://localhost:8080/realms/lumen"
    oidc_client_id: str = "lumen-console"
    oidc_client_secret: str = ""
    oidc_redirect_uri: str = "http://127.0.0.1:5173/callback"

    # Demo mode
    demo_mode: bool = True

    # App
    app_host: str = "127.0.0.1"
    app_port: int = 8000


@lru_cache
def get_settings() -> Settings:
    return Settings()