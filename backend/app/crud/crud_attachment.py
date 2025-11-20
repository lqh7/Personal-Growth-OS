"""
CRUD operations for NoteAttachment entity (Iteration 2).
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models import NoteAttachment
from app.schemas.attachment import AttachmentCreate


def get_attachments_by_note(db: Session, note_id: int) -> List[NoteAttachment]:
    """Get all attachments for a specific note."""
    return db.query(NoteAttachment).filter(NoteAttachment.note_id == note_id).all()


def get_attachment(db: Session, attachment_id: int) -> Optional[NoteAttachment]:
    """Get a specific attachment by ID."""
    return db.query(NoteAttachment).filter(NoteAttachment.id == attachment_id).first()


def create_attachment(db: Session, attachment: AttachmentCreate) -> NoteAttachment:
    """Create a new attachment record."""
    db_attachment = NoteAttachment(
        note_id=attachment.note_id,
        filename=attachment.filename,
        filepath=attachment.filepath,
        filesize=attachment.filesize,
        mimetype=attachment.mimetype
    )
    db.add(db_attachment)
    db.commit()
    db.refresh(db_attachment)
    return db_attachment


def delete_attachment(db: Session, attachment_id: int) -> bool:
    """Delete an attachment record."""
    db_attachment = get_attachment(db, attachment_id)
    if not db_attachment:
        return False
    db.delete(db_attachment)
    db.commit()
    return True


def delete_attachments_by_note(db: Session, note_id: int) -> int:
    """Delete all attachments for a note. Returns number of deleted records."""
    count = db.query(NoteAttachment).filter(NoteAttachment.note_id == note_id).delete()
    db.commit()
    return count
