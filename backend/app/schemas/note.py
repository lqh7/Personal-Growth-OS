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

    # Iteration 1: Core enhancements
    cover_image: Optional[str] = Field(None, max_length=2048, description="Cover image URL")
    emoji: Optional[str] = Field(None, max_length=10, description="Emoji icon (e.g., 📝)")
    is_pinned: bool = Field(False, description="Whether the note is pinned")
    is_favorited: bool = Field(False, description="Whether the note is favorited")
    view_count: int = Field(0, description="Number of times viewed")
    sort_order: int = Field(0, description="Custom sort order weight")


class NoteCreate(NoteBase):
    """Schema for creating a new note."""
    tag_names: List[str] = Field(default_factory=list, description="List of tag names to associate")


class NoteUpdate(BaseModel):
    """Schema for updating an existing note (all fields optional)."""
    title: Optional[str] = Field(None, max_length=500)
    content: Optional[str] = None
    source_url: Optional[str] = Field(None, max_length=2048)
    tag_names: Optional[List[str]] = None

    # Iteration 1: Core enhancements - now updatable
    cover_image: Optional[str] = Field(None, max_length=2048, description="Cover image URL")
    emoji: Optional[str] = Field(None, max_length=10, description="Emoji icon (e.g., 📝)")
    is_pinned: Optional[bool] = Field(None, description="Whether the note is pinned")
    is_favorited: Optional[bool] = Field(None, description="Whether the note is favorited")
    sort_order: Optional[int] = Field(None, description="Custom sort order weight")


class NoteInDB(NoteBase):
    """Schema for note as stored in database."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Note(NoteInDB):
    """Public schema for note with relationships."""
    tags: List[Tag] = []

    model_config = ConfigDict(
        from_attributes=True,
        # Ensure all fields are serialized even with default values
        json_schema_serialization_defaults_required=True
    )


class RelatedNote(BaseModel):
    """Schema for related note returned by RAG."""
    note: Note
    similarity_score: float = Field(..., ge=0.0, le=1.0)


# Pagination schemas
class PaginatedNotes(BaseModel):
    """Paginated response for notes list."""
    items: List[Note]
    total: int = Field(..., description="Total number of notes")
    page: int = Field(..., description="Current page number (1-indexed)")
    size: int = Field(..., description="Page size")
    pages: int = Field(..., description="Total number of pages")


# Batch operation schemas
class BatchNoteIds(BaseModel):
    """Schema for batch operations with note IDs."""
    note_ids: List[int] = Field(..., description="List of note IDs to operate on")


class BatchPinRequest(BatchNoteIds):
    """Schema for batch pin/unpin operation."""
    pinned: bool = Field(..., description="Whether to pin (True) or unpin (False)")


class BatchTagRequest(BatchNoteIds):
    """Schema for batch tag operation."""
    tag_names: List[str] = Field(..., description="List of tag names to add")
    mode: str = Field("add", description="Mode: 'add' to add tags, 'replace' to replace all tags")
