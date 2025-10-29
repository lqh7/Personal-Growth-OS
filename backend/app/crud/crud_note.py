"""
CRUD operations for Note entity.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models import Note, Tag
from app.schemas.note import NoteCreate, NoteUpdate


def get_note(db: Session, note_id: int) -> Optional[Note]:
    """Get a single note by ID."""
    return db.query(Note).filter(Note.id == note_id).first()


def get_notes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None
) -> List[Note]:
    """Get list of notes with optional filtering."""
    query = db.query(Note)

    if project_id is not None:
        query = query.filter(Note.project_id == project_id)

    return query.order_by(Note.updated_at.desc()).offset(skip).limit(limit).all()


def create_note(db: Session, note: NoteCreate) -> Note:
    """Create a new note with tags."""
    # Create the note
    note_data = note.model_dump(exclude={"tag_names"})
    db_note = Note(**note_data)

    # Handle tags
    if note.tag_names:
        for tag_name in note.tag_names:
            # Get or create tag
            db_tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not db_tag:
                db_tag = Tag(name=tag_name)
                db.add(db_tag)
            db_note.tags.append(db_tag)

    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def update_note(db: Session, note_id: int, note_update: NoteUpdate) -> Optional[Note]:
    """Update an existing note."""
    db_note = get_note(db, note_id)
    if not db_note:
        return None

    update_data = note_update.model_dump(exclude_unset=True, exclude={"tag_names"})

    for field, value in update_data.items():
        setattr(db_note, field, value)

    # Update tags if provided
    if note_update.tag_names is not None:
        db_note.tags.clear()
        for tag_name in note_update.tag_names:
            db_tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not db_tag:
                db_tag = Tag(name=tag_name)
                db.add(db_tag)
            db_note.tags.append(db_tag)

    db.commit()
    db.refresh(db_note)
    return db_note


def delete_note(db: Session, note_id: int) -> bool:
    """Delete a note."""
    db_note = get_note(db, note_id)
    if not db_note:
        return False

    db.delete(db_note)
    db.commit()
    return True


def get_tags(db: Session) -> List[Tag]:
    """Get all tags."""
    return db.query(Tag).order_by(Tag.name).all()


def search_notes_by_tag(db: Session, tag_name: str) -> List[Note]:
    """Search notes by tag name."""
    return db.query(Note).join(Note.tags).filter(Tag.name == tag_name).all()
