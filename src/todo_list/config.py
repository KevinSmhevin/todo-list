from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # ─────────────────────────────────────────────────────────────────
    # Database
    # ─────────────────────────────────────────────────────────────────
    
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5434/todos",
        description="POSTGRES SQL connection url"
    )
    sqlalchemy_echo: bool = Field(
        default=False,
        description="Log SQL queries to console"
    )
    sqlalchemy_track_modifications: bool = Field(
        default=False,
        description="Track modifications in SQLAlchemy"
    )
    
    @field_validator('database_url')
    @classmethod
    def validate_db_url(cls, v: str) -> str:
        if not v.startswith(('postgresql://', 'postgresql+psycopg://', 'postgresql+asyncpg://')):
            raise ValueError('database_url must be a PostgreSQL URL')
        return v
    
    # ─────────────────────────────────────────────────────────────────
    # Flask App
    # ─────────────────────────────────────────────────────────────────
    
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        description="Flask secret key for sessions and CSRF"
    )
    
    # ─────────────────────────────────────────────────────────────────
    # Environment
    # ─────────────────────────────────────────────────────────────────
    
    environment: Literal["development", "qa", "production"] = "development"
    debug: bool = False
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    # ─────────────────────────────────────────────────────────────────
    # API Settings
    # ─────────────────────────────────────────────────────────────────
    
    page_size: int = Field(
        default=20,
        description="Default pagination page size"
    )
    max_page_size: int = Field(
        default=100,
        description="Maximum allowed page size"
    )
    
    # ─────────────────────────────────────────────────────────────────
    # CORS Settings
    # ─────────────────────────────────────────────────────────────────
    
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:5173"],
        description="Allowed CORS origins"
    )
    
    # ─────────────────────────────────────────────────────────────────
    # Helper Properties
    # ─────────────────────────────────────────────────────────────────
    
    @property
    def is_production(self) -> bool:
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment == "development"

settings = Settings()

