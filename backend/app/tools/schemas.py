"""
Tool-specific Pydantic schemas for AI tool invocation.
These schemas are designed for LLM tool calling, keeping structures simple.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


# ============================================
# Task Tool Schemas
# ============================================

class TaskIdSchema(BaseModel):
    """Schema for task ID parameter."""
    task_id: int = Field(..., description="The ID of the task")


class TaskListSchema(BaseModel):
    """Schema for listing tasks with optional filters."""
    skip: int = Field(0, ge=0, description="Number of tasks to skip")
    limit: int = Field(20, ge=1, le=100, description="Maximum number of tasks to return")
    project_id: Optional[int] = Field(None, description="Filter by project ID")
    status: Optional[str] = Field(
        None,
        description="Filter by status: pending, in_progress, completed, overdue"
    )


class TaskCreateSchema(BaseModel):
    """Schema for creating a new task."""
    title: str = Field(..., max_length=500, description="Task title")
    description: Optional[str] = Field(None, description="Task description")
    priority: int = Field(3, ge=1, le=5, description="Priority 1-5 (5 is highest)")
    project_id: int = Field(1, description="Project ID (default=1 for '默认' project)")
    due_date: Optional[datetime] = Field(None, description="Due date (ISO 8601 format)")
    start_time: Optional[datetime] = Field(None, description="Scheduled start time")
    end_time: Optional[datetime] = Field(None, description="Scheduled end time")


class TaskUpdateSchema(BaseModel):
    """Schema for updating an existing task."""
    task_id: int = Field(..., description="The ID of the task to update")
    title: Optional[str] = Field(None, max_length=500, description="New task title")
    description: Optional[str] = Field(None, description="New task description")
    status: Optional[str] = Field(
        None,
        description="New status: pending, in_progress, completed"
    )
    priority: Optional[int] = Field(None, ge=1, le=5, description="New priority 1-5")
    due_date: Optional[datetime] = Field(None, description="New due date")
    start_time: Optional[datetime] = Field(None, description="New scheduled start time")
    end_time: Optional[datetime] = Field(None, description="New scheduled end time")
    project_id: Optional[int] = Field(None, description="New project ID")


class TaskSnoozeSchema(BaseModel):
    """Schema for snoozing a task."""
    task_id: int = Field(..., description="The ID of the task to snooze")
    snooze_until: datetime = Field(
        ...,
        description="When to unsnooze the task (ISO 8601 format)"
    )


# ============================================
# Note Tool Schemas
# ============================================

class NoteIdSchema(BaseModel):
    """Schema for note ID parameter."""
    note_id: int = Field(..., description="The ID of the note")


class NoteSearchSchema(BaseModel):
    """Schema for semantic note search."""
    query: str = Field(..., min_length=1, description="Search query text")
    limit: int = Field(5, ge=1, le=20, description="Maximum number of results")


class NoteCreateSchema(BaseModel):
    """Schema for creating a new note."""
    title: str = Field(..., max_length=500, description="Note title")
    content: str = Field(..., description="Note content (Markdown)")
    tag_names: Optional[List[str]] = Field(None, description="List of tag names")
    source_url: Optional[str] = Field(None, description="Source URL if applicable")


class NoteUpdateSchema(BaseModel):
    """Schema for updating an existing note."""
    note_id: int = Field(..., description="The ID of the note to update")
    title: Optional[str] = Field(None, max_length=500, description="New note title")
    content: Optional[str] = Field(None, description="New note content")
    tag_names: Optional[List[str]] = Field(None, description="New list of tag names")


# ============================================
# Link Tool Schemas
# ============================================

class NoteLinkCreateSchema(BaseModel):
    """Schema for creating a link between notes."""
    source_note_id: int = Field(..., description="The source note ID")
    target_note_id: int = Field(..., description="The target note ID to link to")
    link_type: str = Field("reference", description="Type of link (reference, related, etc.)")


class BacklinksSchema(BaseModel):
    """Schema for getting backlinks to a note."""
    note_id: int = Field(..., description="The note ID to find backlinks for")


# ============================================
# UI Command Schemas
# ============================================

class UICommand(BaseModel):
    """
    UI command to be sent to frontend via SSE.
    Used for toast notifications, data refresh, navigation, etc.
    """
    type: Literal["toast", "refresh", "navigate", "modal"] = Field(
        ...,
        description="Command type"
    )
    payload: dict = Field(
        default_factory=dict,
        description="Command payload data"
    )


class ToastPayload(BaseModel):
    """Payload for toast notification."""
    message: str = Field(..., description="Toast message")
    type: Literal["success", "warning", "error", "info"] = Field(
        "success",
        description="Toast type"
    )


class RefreshPayload(BaseModel):
    """Payload for data refresh command."""
    target: Literal["tasks", "notes", "projects", "all"] = Field(
        ...,
        description="Which data to refresh"
    )
