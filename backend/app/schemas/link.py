"""
Pydantic schemas for NoteLink entity (Iteration 3).
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NoteLinkBase(BaseModel):
    """Base schema for note link."""
    source_note_id: int
    target_note_id: int
    link_type: str = "wiki"


class NoteLinkCreate(NoteLinkBase):
    """Schema for creating a note link."""
    pass


class NoteLink(NoteLinkBase):
    """Public schema for note link."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BacklinkResponse(BaseModel):
    """Schema for backlink (reverse link) response."""
    note_id: int
    note_title: str
    link_type: str
    created_at: datetime
