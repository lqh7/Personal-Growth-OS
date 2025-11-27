"""
Task reminder service using APScheduler.
定期扫描即将开始的任务并发送钉钉提醒。
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.database import SessionLocal
from app.db.models import Task, Project
from app.services.dingtalk_service import get_dingtalk_service


class TaskReminderService:
    """Service for checking and sending task reminders."""

    def __init__(self):
        self.dingtalk = get_dingtalk_service()

    def check_and_send_reminders(self):
        """
        Check for tasks starting in 10 minutes and send reminders.
        Called by APScheduler every minute.
        """
        if not self.dingtalk.enabled:
            print("DingTalk reminder is disabled, skipping reminder check")
            return

        db: Session = SessionLocal()
        try:
            now = datetime.now()
            reminder_window_start = now + timedelta(minutes=10)
            reminder_window_end = now + timedelta(minutes=11)

            # Query tasks that need reminders
            tasks = db.query(Task).filter(
                and_(
                    Task.start_time.isnot(None),
                    Task.start_time >= reminder_window_start,
                    Task.start_time < reminder_window_end,
                    Task.status.notin_(['completed', 'archived']),
                    # 防止重复提醒: last_reminder_sent_at 为空 或 早于 (start_time - 10分钟)
                    # 这样如果start_time被修改,可以重新提醒
                    or_(
                        Task.last_reminder_sent_at.is_(None),
                        Task.last_reminder_sent_at < Task.start_time - timedelta(minutes=10)
                    )
                )
            ).all()

            if tasks:
                print(f"Found {len(tasks)} tasks to remind")

            # Send reminders
            for task in tasks:
                # Get project name
                project_name = task.project.name if task.project else None

                # Send reminder
                success = self.dingtalk.send_task_reminder(task, project_name)

                if success:
                    # Update last_reminder_sent_at
                    task.last_reminder_sent_at = now
                    db.commit()
                    print(f"✅ Reminder sent for task {task.id}: {task.title}")
                else:
                    print(f"❌ Failed to send reminder for task {task.id}")

        except Exception as e:
            print(f"Error in task reminder service: {e}")
            db.rollback()
        finally:
            db.close()


# Global singleton
_reminder_service = None

def get_reminder_service() -> TaskReminderService:
    """Get reminder service singleton."""
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = TaskReminderService()
    return _reminder_service
