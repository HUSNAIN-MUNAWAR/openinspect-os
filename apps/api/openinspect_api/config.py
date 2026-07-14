from __future__ import annotations

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OPENINSPECT_", env_file=".env", extra="ignore")
    env: str = "development"
    database_url: str = "sqlite:///./openinspect.db"
    object_root: str = "./object-store"
    jwt_secret: str = "development-only-change-me-32-bytes-minimum"
    access_token_minutes: int = 60
    allowed_origins: str = "http://localhost:3000"

    @property
    def object_path(self) -> Path:
        path = Path(self.object_root)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()
