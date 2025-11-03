"""
CRUD operations for Task entity.
"""
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.models import Task
from app.schemas.task import TaskCreate, TaskUpdate


def get_task(db: Session, task_id: int) -> Optional[Task]:
    """Get a single task by ID."""
    return db.query(Task).filter(Task.id == task_id).first()


def get_tasks(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    include_snoozed: bool = False
) -> List[Task]:
    """
    Get list of tasks with optional filtering.

    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
        project_id: Filter by project ID
        status: Filter by task status
        include_snoozed: If False, exclude tasks with snooze_until > now
    """
    query = db.query(Task).filter(Task.parent_task_id.is_(None))  # Only root tasks

    if project_id is not None:
        query = query.filter(Task.project_id == project_id)

    if status is not None:
        query = query.filter(Task.status == status)

    if not include_snoozed:
        # Exclude tasks that are snoozed (snooze_until is in the future)
        # Uses local time to match frontend timezone (前端时间为准)
        query = query.filter(
            or_(
                Task.snooze_until.is_(None),
                Task.snooze_until <= datetime.now()
            )
        )

    return query.offset(skip).limit(limit).all()


def create_task(db: Session, task: TaskCreate) -> Task:
    """Create a new task."""
    db_task = Task(**task.model_dump())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(db: Session, task_id: int, task_update: TaskUpdate) -> Optional[Task]:
    """Update an existing task."""
    db_task = get_task(db, task_id)
    if not db_task:
        return None

    update_data = task_update.model_dump(exclude_unset=True)

    # If status is being changed to 'completed', set completed_at
    # Uses local time to match frontend timezone (前端时间为准)
    if update_data.get("status") == "completed" and db_task.status != "completed":
        update_data["completed_at"] = datetime.now()

    for field, value in update_data.items():
        setattr(db_task, field, value)

    db.commit()
    db.refresh(db_task)
    return db_task


def delete_task(db: Session, task_id: int) -> bool:
    """Delete a task and all its subtasks."""
    db_task = get_task(db, task_id)
    if not db_task:
        return False

    db.delete(db_task)
    db.commit()
    return True


def snooze_task(db: Session, task_id: int, snooze_until: datetime) -> Optional[Task]:
    """Snooze a task until a specific time."""
    db_task = get_task(db, task_id)
    if not db_task:
        return None

    db_task.snooze_until = snooze_until
    db.commit()
    db.refresh(db_task)
    return db_task
