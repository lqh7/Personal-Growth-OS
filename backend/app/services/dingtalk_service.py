"""
DingTalk notification service for task reminders.
钉钉消息服务,用于发送任务提醒通知。
"""
from typing import Optional
from datetime import datetime

# 直接导入pip安装的DingtalkChatbot
from dingtalkchatbot.chatbot import DingtalkChatbot

from app.core.config import settings
from app.db.models import Task


class DingTalkService:
    """DingTalk message sending service."""

    def __init__(self):
        self.webhook = settings.DINGTALK_WEBHOOK
        self.secret = settings.DINGTALK_SECRET
        self.enabled = settings.ENABLE_TASK_REMINDER and bool(self.webhook)

        if self.enabled:
            self.bot = DingtalkChatbot(
                webhook=self.webhook,
                secret=self.secret if self.secret else None
            )

    def send_task_reminder(self, task: Task, project_name: str = None) -> bool:
        """
        Send task reminder via DingTalk.

        Args:
            task: Task object to remind
            project_name: Optional project name for display

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Format start/end time
            start_str = task.start_time.strftime('%Y-%m-%d %H:%M') if task.start_time else '未设置'
            end_str = task.end_time.strftime('%H:%M') if task.end_time else '未设置'

            # Build markdown message
            title = f"📌 任务提醒: {task.title}"
            content = f"""### 📌 任务提醒

**任务**: {task.title}

**描述**: {task.description or '无'}

**开始时间**: {start_str}
**结束时间**: {end_str}

**项目**: {project_name or '默认'}

---
💡 任务将在10分钟后开始,请做好准备!
"""

            # Send markdown message
            result = self.bot.send_markdown(
                title=title,
                text=content,
                is_at_all=False
            )

            return result.get('errcode') == 0

        except Exception as e:
            print(f"Failed to send DingTalk reminder: {e}")
            return False


# Global singleton instance
_dingtalk_service = None

def get_dingtalk_service() -> DingTalkService:
    """Get DingTalk service singleton instance."""
    global _dingtalk_service
    if _dingtalk_service is None:
        _dingtalk_service = DingTalkService()
    return _dingtalk_service
