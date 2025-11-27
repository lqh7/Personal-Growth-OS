"""
Pydantic schemas for settings management.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class LLMSettingsRead(BaseModel):
    """Schema for reading LLM settings (response)"""
    llm_provider: Literal["openai", "claude", "ollama"] = Field(
        ..., description="LLM provider selection"
    )

    # OpenAI settings
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key")
    openai_api_base: Optional[str] = Field(None, description="OpenAI API Base URL")
    openai_model: Optional[str] = Field(None, description="OpenAI Model Name")

    # Anthropic (Claude) settings
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API Key")
    anthropic_api_base: Optional[str] = Field(None, description="Anthropic API Base URL")
    anthropic_model: Optional[str] = Field(None, description="Anthropic Model Name")

    # Ollama settings
    ollama_base_url: Optional[str] = Field(None, description="Ollama Base URL")
    ollama_model: Optional[str] = Field(None, description="Ollama Model Name")

    # Common settings
    temperature: Optional[float] = Field(0.7, ge=0, le=2, description="Temperature for generation")

    # DingTalk settings
    dingtalk_webhook: Optional[str] = Field("", description="DingTalk webhook URL")
    dingtalk_secret: Optional[str] = Field("", description="DingTalk secret key (optional)")
    enable_task_reminder: bool = Field(True, description="Enable task reminder feature")

    class Config:
        json_schema_extra = {
            "example": {
                "llm_provider": "openai",
                "openai_api_key": "sk-...",
                "openai_api_base": "",
                "openai_model": "gpt-4",
                "temperature": 0.7
            }
        }


class LLMSettingsUpdate(BaseModel):
    """Schema for updating LLM settings (request)"""
    llm_provider: Optional[Literal["openai", "claude", "ollama"]] = Field(
        None, description="LLM provider selection"
    )

    # OpenAI settings
    openai_api_key: Optional[str] = Field(None, description="OpenAI API Key")
    openai_api_base: Optional[str] = Field(None, description="OpenAI API Base URL")
    openai_model: Optional[str] = Field(None, description="OpenAI Model Name")

    # Anthropic (Claude) settings
    anthropic_api_key: Optional[str] = Field(None, description="Anthropic API Key")
    anthropic_api_base: Optional[str] = Field(None, description="Anthropic API Base URL")
    anthropic_model: Optional[str] = Field(None, description="Anthropic Model Name")

    # Ollama settings
    ollama_base_url: Optional[str] = Field(None, description="Ollama Base URL")
    ollama_model: Optional[str] = Field(None, description="Ollama Model Name")

    # Common settings
    temperature: Optional[float] = Field(None, ge=0, le=2, description="Temperature for generation")

    # DingTalk settings
    dingtalk_webhook: Optional[str] = Field(None, description="DingTalk webhook URL")
    dingtalk_secret: Optional[str] = Field(None, description="DingTalk secret key (optional)")
    enable_task_reminder: Optional[bool] = Field(None, description="Enable task reminder feature")

    class Config:
        json_schema_extra = {
            "example": {
                "llm_provider": "openai",
                "openai_api_key": "sk-new-key",
                "openai_model": "gpt-4-turbo"
            }
        }
