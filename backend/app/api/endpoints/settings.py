"""
Settings API endpoints for managing LLM configuration.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict

from app.schemas.settings import LLMSettingsRead, LLMSettingsUpdate
from app.services.settings_service import get_settings_service
from app.core.config import reload_settings

router = APIRouter()


@router.get("/", response_model=LLMSettingsRead)
async def get_llm_settings():
    """
    Get current LLM settings from .env file.

    Returns:
        Current LLM configuration
    """
    try:
        service = get_settings_service()
        env_settings = service.read_env()

        # Map .env keys to response schema
        settings = LLMSettingsRead(
            llm_provider=env_settings.get("LLM_PROVIDER", "openai"),
            openai_api_key=env_settings.get("OPENAI_API_KEY", ""),
            openai_api_base=env_settings.get("OPENAI_API_BASE", ""),
            openai_model=env_settings.get("OPENAI_MODEL", "gpt-4"),
            anthropic_api_key=env_settings.get("ANTHROPIC_API_KEY", ""),
            anthropic_api_base=env_settings.get("ANTHROPIC_API_BASE", ""),
            anthropic_model=env_settings.get("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            ollama_base_url=env_settings.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            ollama_model=env_settings.get("OLLAMA_MODEL", "llama2"),
            temperature=float(env_settings.get("TEMPERATURE", "0.7")),
            dingtalk_webhook=env_settings.get("DINGTALK_WEBHOOK", ""),
            dingtalk_secret=env_settings.get("DINGTALK_SECRET", ""),
            enable_task_reminder=env_settings.get("ENABLE_TASK_REMINDER", "True") == "True",
        )

        return settings

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read settings: {str(e)}")


@router.put("/", response_model=LLMSettingsRead)
async def update_llm_settings(updates: LLMSettingsUpdate):
    """
    Update LLM settings in .env file and apply immediately.

    Args:
        updates: Settings to update (only non-null values will be updated)

    Returns:
        Updated LLM configuration

    Note:
        This updates the .env file and hot-reloads the configuration.
        Changes take effect immediately without requiring backend restart.
    """
    try:
        service = get_settings_service()

        # Build updates dictionary (only non-null values)
        env_updates: Dict[str, str] = {}

        if updates.llm_provider is not None:
            env_updates["LLM_PROVIDER"] = updates.llm_provider

        if updates.openai_api_key is not None:
            env_updates["OPENAI_API_KEY"] = updates.openai_api_key
        if updates.openai_api_base is not None:
            env_updates["OPENAI_API_BASE"] = updates.openai_api_base
        if updates.openai_model is not None:
            env_updates["OPENAI_MODEL"] = updates.openai_model

        if updates.anthropic_api_key is not None:
            env_updates["ANTHROPIC_API_KEY"] = updates.anthropic_api_key
        if updates.anthropic_api_base is not None:
            env_updates["ANTHROPIC_API_BASE"] = updates.anthropic_api_base
        if updates.anthropic_model is not None:
            env_updates["ANTHROPIC_MODEL"] = updates.anthropic_model

        if updates.ollama_base_url is not None:
            env_updates["OLLAMA_BASE_URL"] = updates.ollama_base_url
        if updates.ollama_model is not None:
            env_updates["OLLAMA_MODEL"] = updates.ollama_model

        if updates.temperature is not None:
            env_updates["TEMPERATURE"] = str(updates.temperature)

        # Check if DingTalk settings are being updated
        dingtalk_updated = False
        if updates.dingtalk_webhook is not None:
            env_updates["DINGTALK_WEBHOOK"] = updates.dingtalk_webhook
            dingtalk_updated = True
        if updates.dingtalk_secret is not None:
            env_updates["DINGTALK_SECRET"] = updates.dingtalk_secret
            dingtalk_updated = True
        if updates.enable_task_reminder is not None:
            env_updates["ENABLE_TASK_REMINDER"] = str(updates.enable_task_reminder)
            dingtalk_updated = True

        # Write to .env
        success = service.write_env(env_updates)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to write settings to .env file")

        # Hot-reload settings to apply changes immediately
        reload_settings()

        # Send test message if DingTalk settings were updated and enabled
        if dingtalk_updated and updates.enable_task_reminder:
            try:
                from app.services.dingtalk_service import get_dingtalk_service
                dingtalk = get_dingtalk_service()
                if dingtalk.enabled:
                    dingtalk.bot.send_text(msg="配置已完成", is_at_all=False)
            except Exception as e:
                print(f"Failed to send test message: {e}")
                # Don't fail the whole request if test message fails

        # Return updated settings
        return await get_llm_settings()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")


@router.post("/reload")
async def reload_backend():
    """
    Trigger backend reload to apply new settings.

    Note:
        This endpoint is a placeholder. In production, you would use a process manager
        like systemd, supervisor, or docker to restart the backend.

    Returns:
        Message indicating manual restart is required
    """
    return {
        "message": "Settings updated. Please manually restart the backend server for changes to take effect.",
        "command": "cd backend && python -m uvicorn app.main:app --reload"
    }
