"""
Task reminder service using APScheduler.
定期扫描即将开始和刚结束的任务并发送钉钉提醒。
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.database import SessionLocal
from app.db.models import Task, Project
from app.services.dingtalk_service import get_dingtalk_service

logger = logging.getLogger(__name__)


class TaskReminderService:
    """Service for checking and sending task reminders."""

    def __init__(self):
        # 不再在初始化时缓存 dingtalk 服务
        # 每次使用时动态获取，以支持配置热重载
        pass

    @property
    def dingtalk(self):
        """动态获取 dingtalk 服务，支持配置热重载。"""
        return get_dingtalk_service()

    def check_and_send_missed_reminders(self):
        """
        Check for tasks that should have been reminded during service downtime.
        Called once during scheduler initialization.

        Scans tasks with start_time in [now-10min, now] that haven't been reminded.
        This ensures missed reminders are sent when the service restarts.
        """
        if not self.dingtalk.enabled:
            return

        db: Session = SessionLocal()
        try:
            now = datetime.now()
            # Check past 10 minutes for missed start reminders
            past_reminder_window_start = now - timedelta(minutes=10)

            # Query tasks that should have been reminded in the past 10 minutes
            tasks = db.query(Task).filter(
                and_(
                    Task.start_time.isnot(None),
                    Task.start_time >= past_reminder_window_start,
                    Task.start_time <= now,
                    Task.status.notin_(['completed', 'archived']),
                    or_(
                        Task.last_reminder_sent_at.is_(None),
                        Task.last_reminder_sent_at < Task.start_time - timedelta(minutes=10)
                    )
                )
            ).all()

            # Send missed start reminders
            for task in tasks:
                project_name = task.project.name if task.project else None
                success = self.dingtalk.send_task_start_reminder(task, project_name)

                if success:
                    task.last_reminder_sent_at = now
                    db.commit()
                    logger.info(f"[Startup] Sent missed start reminder for task: {task.title}")

            # Also check for missed end reminders (tasks that ended in the past 10 minutes)
            self._send_missed_end_reminders(db, now)

        except Exception as e:
            logger.error(f"Error checking missed reminders: {e}")
            db.rollback()
        finally:
            db.close()

    def _send_missed_end_reminders(self, db: Session, now: datetime):
        """Send missed end reminders for tasks that ended during downtime."""
        past_window_start = now - timedelta(minutes=10)

        tasks = db.query(Task).filter(
            and_(
                Task.end_time.isnot(None),
                Task.end_time >= past_window_start,
                Task.end_time <= now,
                Task.status.notin_(['completed', 'archived']),
                or_(
                    Task.last_end_reminder_sent_at.is_(None),
                    Task.last_end_reminder_sent_at < Task.end_time
                )
            )
        ).all()

        for task in tasks:
            project_name = task.project.name if task.project else None
            success = self.dingtalk.send_task_end_reminder(task, project_name)

            if success:
                task.last_end_reminder_sent_at = now
                db.commit()
                logger.info(f"[Startup] Sent missed end reminder for task: {task.title}")

    def check_and_send_reminders(self):
        """
        Check for tasks starting in 10 minutes AND tasks ending now, send reminders.
        Called by APScheduler every minute.
        """
        if not self.dingtalk.enabled:
            return

        db: Session = SessionLocal()
        try:
            now = datetime.now()

            # 1. Send START reminders (10-11 minutes before start_time)
            self._send_start_reminders(db, now)

            # 2. Send END reminders (when end_time is reached)
            self._send_end_reminders(db, now)

        except Exception as e:
            logger.error(f"Error in check_and_send_reminders: {e}")
            db.rollback()
        finally:
            db.close()

    def _send_start_reminders(self, db: Session, now: datetime):
        """Send start reminders for tasks starting in 10-11 minutes."""
        reminder_window_start = now + timedelta(minutes=10)
        reminder_window_end = now + timedelta(minutes=11)

        # Query tasks that need start reminders
        tasks = db.query(Task).filter(
            and_(
                Task.start_time.isnot(None),
                Task.start_time >= reminder_window_start,
                Task.start_time < reminder_window_end,
                Task.status.notin_(['completed', 'archived']),
                # 防止重复提醒
                or_(
                    Task.last_reminder_sent_at.is_(None),
                    Task.last_reminder_sent_at < Task.start_time - timedelta(minutes=10)
                )
            )
        ).all()

        # Send start reminders
        for task in tasks:
            project_name = task.project.name if task.project else None
            success = self.dingtalk.send_task_start_reminder(task, project_name)

            if success:
                task.last_reminder_sent_at = now
                db.commit()
                logger.info(f"Sent start reminder for task: {task.title}")

    def _send_end_reminders(self, db: Session, now: datetime):
        """Send end reminders for tasks whose end_time just passed (within last minute)."""
        # 查询 end_time 在过去1分钟内的任务
        end_window_start = now - timedelta(minutes=1)
        end_window_end = now

        tasks = db.query(Task).filter(
            and_(
                Task.end_time.isnot(None),
                Task.end_time >= end_window_start,
                Task.end_time < end_window_end,
                Task.status.notin_(['completed', 'archived']),
                # 防止重复提醒：未发送过结束提醒，或上次发送时间早于当前end_time
                or_(
                    Task.last_end_reminder_sent_at.is_(None),
                    Task.last_end_reminder_sent_at < Task.end_time
                )
            )
        ).all()

        # Send end reminders
        for task in tasks:
            project_name = task.project.name if task.project else None
            success = self.dingtalk.send_task_end_reminder(task, project_name)

            if success:
                task.last_end_reminder_sent_at = now
                db.commit()
                logger.info(f"Sent end reminder for task: {task.title}")


# Global singleton
_reminder_service = None

def get_reminder_service() -> TaskReminderService:
    """Get reminder service singleton."""
    global _reminder_service
    if _reminder_service is None:
        _reminder_service = TaskReminderService()
    return _reminder_service
