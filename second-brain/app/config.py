"""Application configuration."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Second Brain"
    app_version: str = "1.0.0"
    debug: bool = False

    database_url: str = "sqlite:///./second_brain.db"
    db_echo: bool = False


settings = Settings()
