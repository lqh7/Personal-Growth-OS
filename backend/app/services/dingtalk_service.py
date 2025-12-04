"""
DingTalk notification service for task reminders.
钉钉消息服务,用于发送任务提醒通知。
"""
from typing import Optional
from datetime import datetime
import logging

# 直接导入pip安装的DingtalkChatbot
from dingtalkchatbot.chatbot import DingtalkChatbot

from app.core import config
from app.db.models import Task

logger = logging.getLogger(__name__)


class DingTalkService:
    """DingTalk message sending service."""

    def __init__(self):
        # 使用 config.settings 而不是直接导入 settings
        # 这样在 reload_settings() 后可以获取最新的配置
        current_settings = config.settings
        self.webhook = current_settings.DINGTALK_WEBHOOK
        self.secret = current_settings.DINGTALK_SECRET
        self.enabled = current_settings.ENABLE_TASK_REMINDER and bool(self.webhook)
        self.bot = None  # 始终初始化，避免 AttributeError

        if self.enabled:
            self.bot = DingtalkChatbot(
                webhook=self.webhook,
                secret=self.secret if self.secret else None
            )
            logger.info(f"DingTalk service initialized: webhook={bool(self.webhook)}, secret={bool(self.secret)}")

    def send_task_start_reminder(self, task: Task, project_name: str = None) -> bool:
        """
        Send task START reminder via DingTalk.

        Args:
            task: Task object to remind
            project_name: Optional project name for display

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled or not self.bot:
            return False

        try:
            # Format times
            start_str = task.start_time.strftime('%Y-%m-%d %H:%M') if task.start_time else '未设置'
            end_str = task.end_time.strftime('%Y-%m-%d %H:%M') if task.end_time else '未设置'
            description = task.description or '暂无描述'

            # 动态计算距离开始的时间
            now = datetime.now()
            if task.start_time:
                minutes_until_start = int((task.start_time - now).total_seconds() / 60)
                if minutes_until_start <= 0:
                    time_hint = "任务即将开始"
                elif minutes_until_start == 1:
                    time_hint = f"任务将在 **1分钟后** 开始"
                else:
                    time_hint = f"任务将在 **{minutes_until_start}分钟后** 开始"
            else:
                time_hint = "任务即将开始"

            # Build beautiful markdown message
            title = f"⏰ 任务即将开始: {task.title}"
            content = f"""## ⏰ 任务即将开始

---

🎯 **任务名称**

> {task.title}

📝 **任务描述**

> {description}

⏱️ **时间安排**

> 🟢 开始：{start_str}
>
> 🔴 结束：{end_str}

📂 **所属项目**

> {project_name or '默认'}

---

💡 **温馨提示**：{time_hint}，请做好准备！
"""

            result = self.bot.send_markdown(
                title=title,
                text=content,
                is_at_all=False
            )

            success = result.get('errcode') == 0
            if success:
                logger.info(f"Start reminder sent for task: {task.title}")
            else:
                logger.error(f"Failed to send start reminder: {result}")
            return success

        except Exception as e:
            logger.error(f"Failed to send task start reminder: {e}")
            return False

    def send_task_end_reminder(self, task: Task, project_name: str = None) -> bool:
        """
        Send task END reminder via DingTalk (when end_time is reached).

        Args:
            task: Task object to remind
            project_name: Optional project name for display

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled or not self.bot:
            return False

        try:
            # Format times
            start_str = task.start_time.strftime('%Y-%m-%d %H:%M') if task.start_time else '未设置'
            end_str = task.end_time.strftime('%Y-%m-%d %H:%M') if task.end_time else '未设置'

            # Build beautiful markdown message
            title = f"✅ 任务时间已到: {task.title}"
            content = f"""## ✅ 任务时间已到

---

🎯 **任务名称**

> {task.title}

⏱️ **时间安排**

> 🟢 开始：{start_str}
>
> 🔴 结束：{end_str}（已到时间）

📂 **所属项目**

> {project_name or '默认'}

---

🎉 **任务时间结束**，请检查完成情况并更新任务状态！
"""

            result = self.bot.send_markdown(
                title=title,
                text=content,
                is_at_all=False
            )

            success = result.get('errcode') == 0
            if success:
                logger.info(f"End reminder sent for task: {task.title}")
            else:
                logger.error(f"Failed to send end reminder: {result}")
            return success

        except Exception as e:
            logger.error(f"Failed to send task end reminder: {e}")
            return False

    # 保留旧方法名作为别名，兼容现有代码
    def send_task_reminder(self, task: Task, project_name: str = None) -> bool:
        """Alias for send_task_start_reminder for backward compatibility."""
        return self.send_task_start_reminder(task, project_name)

    def send_text(self, msg: str) -> bool:
        """
        Send a simple text message via DingTalk.

        Args:
            msg: Text message to send

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled or not self.bot:
            logger.warning(f"DingTalk not enabled or bot not initialized. enabled={self.enabled}, bot={self.bot is not None}")
            return False

        try:
            result = self.bot.send_text(msg=msg, is_at_all=False)
            success = result.get('errcode') == 0
            if success:
                logger.info(f"DingTalk text message sent successfully: {msg[:50]}...")
            else:
                logger.error(f"DingTalk API error: {result}")
            return success
        except Exception as e:
            logger.error(f"Failed to send DingTalk text message: {e}")
            return False


# Global singleton instance
_dingtalk_service = None

def get_dingtalk_service() -> DingTalkService:
    """Get DingTalk service singleton instance."""
    global _dingtalk_service
    if _dingtalk_service is None:
        _dingtalk_service = DingTalkService()
    return _dingtalk_service


def reload_dingtalk_service() -> DingTalkService:
    """
    Reload DingTalk service with latest configuration.
    Called after settings are updated to apply new webhook/secret.
    """
    global _dingtalk_service
    _dingtalk_service = DingTalkService()
    logger.info(f"DingTalk service reloaded: enabled={_dingtalk_service.enabled}")
    return _dingtalk_service
