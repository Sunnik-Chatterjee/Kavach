"""Application configuration via Pydantic Settings.

All values are loaded from environment variables / .env. Nothing is hardcoded.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # model_path is a legitimate field name; silence the protected
        # namespace warning from pydantic.
        protected_namespaces=(),
    )

    # --- App ---
    app_name: str = "Kavach Backend"
    app_version: str = "1.0.0"
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = True

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Database ---
    database_url: str = Field(
        default="",
        description="Neon PostgreSQL async connection string.",
    )

    # --- Neon ---
    neon_project_id: str = ""
    neon_database_name: str = ""

    # --- CORS ---
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated list of allowed CORS origins.",
    )

    # --- ML config ---
    model_path: str = ""
    window_size: int = 90

    # --- Serial config ---
    com_port: str = ""
    baud_rate: int = 460800

    # --- WebSocket ---
    ws_heartbeat_interval: int = 30

    # --- Logging ---
    log_level: str = "INFO"

    # --- Security ---
    secret_key: str = ""
    access_token_expire_minutes: int = 60

    @property
    def cors_origin_list(self) -> list[str]:
        """Return the parsed CORS origins as a list."""
        if isinstance(self.cors_origins, str):
            cleaned = self.cors_origins.strip().strip("[]").replace('"', "").replace("'", "")
            return [o.strip() for o in cleaned.split(",") if o.strip()]
        return list(self.cors_origins)


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()