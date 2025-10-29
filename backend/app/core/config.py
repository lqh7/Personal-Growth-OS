"""
Application configuration management using Pydantic Settings.
"""
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Personal Growth OS"
    DEBUG: bool = False
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

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
        case_sensitive=True
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance
settings = get_settings()
