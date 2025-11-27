"""
APScheduler integration for task reminders (v3.10.4).
集成APScheduler 3.10.4版本用于任务提醒调度。
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor

from app.core.config import settings
from app.services.task_reminder_service import get_reminder_service


# Global scheduler instance
scheduler: BackgroundScheduler = None


def init_scheduler():
    """Initialize and start APScheduler v3."""
    global scheduler

    if not settings.ENABLE_TASK_REMINDER:
        print("Task reminder is disabled in settings")
        return

    try:
        # Configure job stores (PostgreSQL persistence)
        jobstores = {
            'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
        }

        # Configure executors
        executors = {
            'default': ThreadPoolExecutor(max_workers=10)
        }

        # Job defaults
        job_defaults = {
            'coalesce': True,  # Combine multiple missed executions into one
            'max_instances': 1,  # Only one instance of the job at a time
            'misfire_grace_time': 60  # Allow 60s grace for late execution
        }

        # Create scheduler with PostgreSQL persistence
        scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'  # 设置时区
        )

        # Add job: check every minute
        reminder_service = get_reminder_service()
        scheduler.add_job(
            func=reminder_service.check_and_send_reminders,
            trigger='interval',
            minutes=1,
            id='task_reminder_checker',
            name='Check and send task reminders',
            replace_existing=True
        )

        # Start scheduler
        scheduler.start()
        print("[OK] APScheduler 3.10.4 started with PostgreSQL persistence")
        print("[OK] Task reminder service is running - checking every minute")

    except Exception as e:
        print(f"[ERROR] Failed to start APScheduler: {e}")
        raise


def shutdown_scheduler():
    """Shutdown APScheduler."""
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)
        print("APScheduler shut down")
