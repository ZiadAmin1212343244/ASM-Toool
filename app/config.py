"""Application settings loaded from environment / .env."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Third-Party Attack Surface Monitor"
    app_env: str = "development"
    secret_key: str = "dev-secret-change-me"
    fernet_key: str = ""

    host: str = "127.0.0.1"
    port: int = 8000
    open_browser: bool = True

    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'tpm.db'}"

    session_cookie_name: str = "tpm_session"
    session_max_age_seconds: int = 28800

    file_storage_path: str = str(BASE_DIR / "data" / "files")
    max_upload_mb: int = 25

    leak_retention_days: int = 180

    shodan_api_key: str = ""
    censys_api_id: str = ""
    censys_api_secret: str = ""
    hibp_api_key: str = ""
    github_token: str = ""

    scan_rate_limit_rps: float = 5.0

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def file_storage(self) -> Path:
        return Path(self.file_storage_path)


@lru_cache
def get_settings() -> Settings:
    return Settings()
