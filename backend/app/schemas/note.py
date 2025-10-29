"""
Pydantic schemas for Note entity.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, HttpUrl


class TagBase(BaseModel):
    """Base schema for Tag."""
    name: str = Field(..., max_length=100)
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")


class TagCreate(TagBase):
    """Schema for creating a new tag."""
    pass


class Tag(TagBase):
    """Public schema for tag."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NoteBase(BaseModel):
    """Base schema for Note with common fields."""
    title: str = Field(..., max_length=500)
    content: str = Field(..., description="Full note content in Markdown")
    source_url: Optional[str] = Field(None, max_length=2048, description="Source URL for traceability")
    project_id: Optional[int] = None


class NoteCreate(NoteBase):
    """Schema for creating a new note."""
    tag_names: List[str] = Field(default_factory=list, description="List of tag names to associate")


class NoteUpdate(BaseModel):
    """Schema for updating an existing note (all fields optional)."""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    source_url: Optional[str] = Field(None, max_length=2048)
    project_id: Optional[int] = None
    tag_names: Optional[List[str]] = None


class NoteInDB(NoteBase):
    """Schema for note as stored in database."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Note(NoteInDB):
    """Public schema for note with relationships."""
    tags: List[Tag] = []

    model_config = ConfigDict(from_attributes=True)


class RelatedNote(BaseModel):
    """Schema for related note returned by RAG."""
    note: Note
    similarity_score: float = Field(..., ge=0.0, le=1.0)
