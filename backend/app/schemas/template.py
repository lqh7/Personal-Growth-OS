"""
Pydantic schemas for NoteTemplate entity (Iteration 2).
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TemplateBase(BaseModel):
    """Base schema for template."""
    name: str = Field(..., max_length=200, description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    content_template: str = Field(..., description="Markdown template with placeholders")
    icon: Optional[str] = Field(None, max_length=10, description="Emoji icon")
    category: Optional[str] = Field(None, max_length=100, description="Template category")


class TemplateCreate(TemplateBase):
    """Schema for creating a new template."""
    pass


class TemplateUpdate(BaseModel):
    """Schema for updating template (all fields optional)."""
    name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    content_template: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=10)
    category: Optional[str] = Field(None, max_length=100)


class Template(TemplateBase):
    """Public schema for template."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
