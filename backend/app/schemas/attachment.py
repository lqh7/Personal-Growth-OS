"""
Pydantic schemas for NoteAttachment entity (Iteration 2).
"""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AttachmentBase(BaseModel):
    """Base schema for attachment."""
    filename: str = Field(..., max_length=255, description="Original filename")
    mimetype: str = Field(..., max_length=100, description="MIME type (e.g., image/png)")


class AttachmentCreate(AttachmentBase):
    """Schema for creating attachment (internal use - from file upload)."""
    note_id: int
    filepath: str = Field(..., max_length=512)
    filesize: int = Field(..., gt=0, description="File size in bytes")


class Attachment(AttachmentBase):
    """Public schema for attachment."""
    id: int
    note_id: int
    filepath: str
    filesize: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
