"""
CRUD operations for Note entity.
"""
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload

from app.db.models import Note, Tag, SearchHistory
from app.schemas.note import NoteCreate, NoteUpdate, SearchHistoryCreate


def get_note(db: Session, note_id: int) -> Optional[Note]:
    """Get a single note by ID with tags loaded."""
    return (
        db.query(Note)
        .options(joinedload(Note.tags))
        .filter(Note.id == note_id)
        .first()
    )


def get_notes(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    project_id: Optional[int] = None
) -> List[Note]:
    """Get list of notes with tags loaded."""
    query = (
        db.query(Note)
        .options(joinedload(Note.tags))
    )

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


def search_notes_by_text(db: Session, query: str, limit: int = 20) -> List[Note]:
    """
    Search notes by text query (title and content).
    Simple text search as fallback when semantic search is unavailable.
    Uses LIKE for better Chinese character support.
    """
    search_term = f"%{query}%"
    return (
        db.query(Note)
        .options(joinedload(Note.tags))
        .filter(
            (Note.title.like(search_term)) |
            (Note.content.like(search_term))
        )
        .order_by(Note.updated_at.desc())
        .limit(limit)
        .all()
    )


# Iteration 1: Core enhancements

def toggle_note_pin(db: Session, note_id: int, pinned: bool) -> Optional[Note]:
    """Toggle note pinned status."""
    db_note = get_note(db, note_id)
    if not db_note:
        return None

    db_note.is_pinned = pinned
    db.commit()
    db.refresh(db_note)
    return db_note


def toggle_note_favorite(db: Session, note_id: int, favorited: bool) -> Optional[Note]:
    """Toggle note favorited status."""
    db_note = get_note(db, note_id)
    if not db_note:
        return None

    db_note.is_favorited = favorited
    db.commit()
    db.refresh(db_note)
    return db_note


def increment_note_view_count(db: Session, note_id: int) -> Optional[Note]:
    """Increment note view count."""
    db_note = get_note(db, note_id)
    if not db_note:
        return None

    db_note.view_count += 1
    db.commit()
    db.refresh(db_note)
    return db_note


# Search History operations

def create_search_history(db: Session, query_text: str, result_count: int) -> SearchHistory:
    """Create a new search history entry."""
    db_search = SearchHistory(query_text=query_text, result_count=result_count)
    db.add(db_search)
    db.commit()
    db.refresh(db_search)
    return db_search


def get_search_history(db: Session, limit: int = 10) -> List[SearchHistory]:
    """Get recent search history entries."""
    return (
        db.query(SearchHistory)
        .order_by(SearchHistory.timestamp.desc())
        .limit(limit)
        .all()
    )
