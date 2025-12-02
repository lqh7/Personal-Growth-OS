"""
Settings API endpoints for managing LLM configuration.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict
from datetime import datetime
import logging

from app.schemas.settings import LLMSettingsRead, LLMSettingsUpdate
from app.services.settings_service import get_settings_service
from app.core.config import reload_settings

logger = logging.getLogger(__name__)

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
            ollama_api_key=env_settings.get("OLLAMA_API_KEY", ""),
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

        if updates.ollama_api_key is not None:
            env_updates["OLLAMA_API_KEY"] = updates.ollama_api_key
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

        # Reload DingTalk service singleton with new settings
        if dingtalk_updated:
            try:
                from app.services.dingtalk_service import reload_dingtalk_service
                dingtalk = reload_dingtalk_service()  # Reload singleton with new settings
                logger.info(f"DingTalk config updated: enabled={dingtalk.enabled}, webhook={bool(dingtalk.webhook)}")
            except Exception as e:
                logger.error(f"DingTalk service reload error: {e}")

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


@router.post("/test-dingtalk")
async def test_dingtalk_notification(request: dict):
    """
    Test DingTalk notification configuration.

    发送测试消息验证钉钉webhook配置是否正确。

    Args:
        request: { "webhook": str, "secret": str }

    Returns:
        { "success": bool, "error": str }
    """
    try:
        webhook = request.get("webhook", "").strip()
        secret = request.get("secret", "").strip()

        if not webhook:
            return {"success": False, "error": "Webhook URL 不能为空"}

        # 临时创建 DingTalkService 实例进行测试（不影响全局单例）
        from dingtalkchatbot.chatbot import DingtalkChatbot

        # 记录请求参数（隐藏敏感信息）
        logger.info(f"Testing DingTalk webhook: {webhook[:60]}... (secret={'present' if secret else 'absent'})")

        test_bot = DingtalkChatbot(
            webhook=webhook,
            secret=secret if secret else None
        )

        # 发送测试消息
        test_message = """🔔 Personal Growth OS 配置测试

这是一条测试消息，用于验证钉钉机器人配置是否正确。

如果您看到此消息，说明配置成功！✅

---
发送时间：{time}
""".format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        result = test_bot.send_text(msg=test_message, is_at_all=False)

        # 记录完整API响应
        logger.info(f"DingTalk API response: {result}")

        if result.get('errcode') == 0:
            logger.info("DingTalk test message sent successfully")
            return {"success": True}
        else:
            error_msg = result.get('errmsg', '未知错误')
            errcode = result.get('errcode', 'unknown')
            # 返回错误码帮助诊断
            logger.error(f"DingTalk test failed with errcode={errcode}: {error_msg}")
            return {"success": False, "error": f"钉钉API错误 [code={errcode}]: {error_msg}"}

    except Exception as e:
        # 记录异常类型
        logger.error(f"DingTalk test exception: {type(e).__name__}: {e}")
        return {"success": False, "error": f"请求异常 ({type(e).__name__}): {str(e)}"}
