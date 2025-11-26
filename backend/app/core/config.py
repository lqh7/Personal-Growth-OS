"""
Application configuration management using Pydantic Settings.
"""
from typing import List, Union
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from functools import lru_cache


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

    # Database
    DATABASE_URL: str = "sqlite:///./personal_growth_os.db"

    # ChromaDB
    CHROMA_PERSIST_DIRECTORY: str = "./chroma_data"

    # Mem0
    MEM0_PERSIST_DIRECTORY: str = "./mem0_data"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"  # Ignore extra fields in .env to allow hot-reload
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def reload_settings():
    """
    Reload settings from .env file by clearing cache and creating new instance.
    This allows runtime configuration updates without restarting the service.
    """
    global settings
    # Clear the lru_cache to force re-reading from .env
    get_settings.cache_clear()
    # Create new settings instance
    settings = get_settings()
    return settings


# Global settings instance
settings = get_settings()
