"""
CRUD operations for NoteLink entity (Iteration 3).
"""
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.models import NoteLink, Note
from app.schemas.link import NoteLinkCreate


def create_link(db: Session, link: NoteLinkCreate) -> NoteLink:
    """Create a bidirectional link between two notes."""
    # Check if link already exists
    existing = db.query(NoteLink).filter(
        NoteLink.source_note_id == link.source_note_id,
        NoteLink.target_note_id == link.target_note_id
    ).first()

    if existing:
        return existing

    db_link = NoteLink(
        source_note_id=link.source_note_id,
        target_note_id=link.target_note_id,
        link_type=link.link_type
    )
    db.add(db_link)
    db.commit()
    db.refresh(db_link)
    return db_link


def get_outgoing_links(db: Session, note_id: int) -> List[NoteLink]:
    """Get all links from this note to other notes."""
    return db.query(NoteLink).filter(NoteLink.source_note_id == note_id).all()


def get_backlinks(db: Session, note_id: int) -> List[dict]:
    """Get all notes that link to this note (backlinks)."""
    links = db.query(NoteLink, Note).join(
        Note, NoteLink.source_note_id == Note.id
    ).filter(NoteLink.target_note_id == note_id).all()

    return [
        {
            "note_id": note.id,
            "note_title": note.title,
            "link_type": link.link_type,
            "created_at": link.created_at
        }
        for link, note in links
    ]


def delete_link(db: Session, source_note_id: int, target_note_id: int) -> bool:
    """Delete a specific link."""
    link = db.query(NoteLink).filter(
        NoteLink.source_note_id == source_note_id,
        NoteLink.target_note_id == target_note_id
    ).first()

    if not link:
        return False

    db.delete(link)
    db.commit()
    return True


def parse_wiki_links(content: str) -> List[str]:
    """
    Parse wiki-style links [[Title]] from note content.
    Returns list of note titles.
    """
    import re
    pattern = r'\[\[([^\]]+)\]\]'
    matches = re.findall(pattern, content)
    return matches


def sync_note_links(db: Session, note_id: int, content: str):
    """
    Synchronize note links based on wiki-style links in content.
    Removes old links and creates new ones.
    """
    # Parse wiki links from content
    wiki_titles = parse_wiki_links(content)

    # Find target notes by title
    target_notes = db.query(Note).filter(Note.title.in_(wiki_titles)).all()
    target_note_ids = {note.id for note in target_notes}

    # Get existing outgoing links
    existing_links = db.query(NoteLink).filter(NoteLink.source_note_id == note_id).all()
    existing_target_ids = {link.target_note_id for link in existing_links}

    # Delete links that no longer exist in content
    links_to_delete = existing_target_ids - target_note_ids
    if links_to_delete:
        db.query(NoteLink).filter(
            NoteLink.source_note_id == note_id,
            NoteLink.target_note_id.in_(links_to_delete)
        ).delete(synchronize_session=False)

    # Create new links
    links_to_create = target_note_ids - existing_target_ids
    for target_id in links_to_create:
        link = NoteLink(
            source_note_id=note_id,
            target_note_id=target_id,
            link_type="wiki"
        )
        db.add(link)

    db.commit()
