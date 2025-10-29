"""
Pydantic schemas for Task entity.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class TaskBase(BaseModel):
    """Base schema for Task with common fields."""
    title: str = Field(..., max_length=500)
    description: Optional[str] = None
    status: str = Field(default="pending", pattern="^(pending|in_progress|completed|cancelled)$")
    priority: int = Field(default=3, ge=1, le=5)
    due_date: Optional[datetime] = None
    snooze_until: Optional[datetime] = None
    parent_task_id: Optional[int] = None
    project_id: Optional[int] = None


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    pass


class TaskUpdate(BaseModel):
    """Schema for updating an existing task (all fields optional)."""
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|in_progress|completed|cancelled)$")
    priority: Optional[int] = Field(None, ge=1, le=5)
    due_date: Optional[datetime] = None
    snooze_until: Optional[datetime] = None
    parent_task_id: Optional[int] = None
    project_id: Optional[int] = None


class TaskInDB(TaskBase):
    """Schema for task as stored in database."""
    id: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Task(TaskInDB):
    """Public schema for task with relationships."""
    subtasks: List["Task"] = []

    model_config = ConfigDict(from_attributes=True)


class TaskIgnitionRequest(BaseModel):
    """
    Request schema for Task Ignition Ritual.
    用户输入模糊的大任务，系统自动分解。
    """
    task_description: str = Field(
        ...,
        description="User's vague or large task description",
        min_length=5
    )
    project_id: Optional[int] = None


class TaskIgnitionResponse(BaseModel):
    """
    Response schema for Task Ignition Ritual.
    返回分解后的任务列表和最小可行启动任务。
    """
    main_task: Task
    subtasks: List[Task]
    minimum_viable_task: Task
    related_notes: List[dict] = []  # Simplified for MVP
