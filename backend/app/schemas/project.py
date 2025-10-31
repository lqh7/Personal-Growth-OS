"""
Pydantic schemas for Project entity.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProjectBase(BaseModel):
    """Base schema for Project with common fields."""
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(default="#667eea", max_length=7)


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating an existing project."""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7)


class Project(ProjectBase):
    """Public schema for project."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
