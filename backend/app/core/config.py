"""
Application configuration management using Pydantic Settings.
"""
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict, PydanticBaseSettingsSource
from pydantic import field_validator
from functools import lru_cache
from typing import Any, Tuple, Type


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Personal Growth OS"
    DEBUG: bool = False
    CORS_ORIGINS: Union[List[str], str] = ["http://localhost:5173", "http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS_ORIGINS from comma-separated string or JSON list."""
        if isinstance(v, str):
            # If it's a comma-separated string, split it
            if "," in v and not v.startswith("["):
                return [origin.strip() for origin in v.split(",")]
            # Otherwise try to parse as JSON (will be handled by pydantic)
        return v

    # LLM Configuration
    LLM_PROVIDER: str = "openai"  # openai, claude, ollama

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = ""  # Custom API base URL (optional)
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Claude (Anthropic)
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_API_BASE: str = ""  # Custom API base URL (optional)
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"

    # Ollama (Local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"

    # Common LLM Settings
    TEMPERATURE: float = 0.7

    # Embedding Model
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    # Database - PostgreSQL + pgvector
    # Format: postgresql://username:password@host:port/database_name
    DATABASE_URL: str = "postgresql://localhost/personal_growth_os"

    # DingTalk Configuration
    DINGTALK_WEBHOOK: str = ""
    DINGTALK_SECRET: str = ""
    ENABLE_TASK_REMINDER: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields in .env to allow hot-reload
        env_prefix="",  # No prefix
        validate_default=True
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """
        Customize settings sources priority.

        Prioritize .env file over environment variables to avoid shell environment
        variables (like Claude Code's OPENAI_API_KEY) from overriding .env config.

        Priority (highest to lowest):
        1. init_settings (passed to __init__)
        2. dotenv_settings (.env file) <- PRIORITIZED
        3. env_settings (environment variables)
        4. file_secret_settings (secrets file)
        """
        return init_settings, dotenv_settings, env_settings, file_secret_settings


# DO NOT use lru_cache - it causes stale config issues
def get_settings() -> Settings:
    """Get settings instance (not cached to avoid stale config)."""
    return Settings()


def reload_settings():
    """
    Reload settings from .env file by creating new instance.
    This allows runtime configuration updates without restarting the service.
    """
    global settings
    # Create new settings instance
    settings = Settings()
    return settings


# Global settings instance - will be fresh on import
settings = Settings()
