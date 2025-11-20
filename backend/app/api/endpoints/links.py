"""
Note links management API endpoints (Iteration 3).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.link import NoteLink, NoteLinkCreate, BacklinkResponse
from app.crud import crud_link, crud_note

router = APIRouter()


@router.post("/", response_model=NoteLink, status_code=status.HTTP_201_CREATED)
def create_link(link: NoteLinkCreate, db: Session = Depends(get_db)):
    """
    Create a bidirectional link between two notes.

    - **source_note_id**: The note containing the link
    - **target_note_id**: The note being linked to
    - **link_type**: Type of link (default: "wiki")
    """
    # Verify both notes exist
    source_note = crud_note.get_note(db, link.source_note_id)
    target_note = crud_note.get_note(db, link.target_note_id)

    if not source_note:
        raise HTTPException(status_code=404, detail="Source note not found")
    if not target_note:
        raise HTTPException(status_code=404, detail="Target note not found")

    return crud_link.create_link(db, link)


@router.get("/note/{note_id}/outgoing", response_model=List[NoteLink])
def get_outgoing_links(note_id: int, db: Session = Depends(get_db)):
    """Get all links from this note to other notes."""
    note = crud_note.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return crud_link.get_outgoing_links(db, note_id)


@router.get("/note/{note_id}/backlinks", response_model=List[BacklinkResponse])
def get_backlinks(note_id: int, db: Session = Depends(get_db)):
    """
    Get all notes that link to this note (backlinks/reverse links).

    This enables navigation of the knowledge graph in reverse.
    """
    note = crud_note.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return crud_link.get_backlinks(db, note_id)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_link(source_note_id: int, target_note_id: int, db: Session = Depends(get_db)):
    """Delete a specific link between two notes."""
    success = crud_link.delete_link(db, source_note_id, target_note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Link not found")


@router.post("/note/{note_id}/sync", status_code=status.HTTP_200_OK)
def sync_note_links(note_id: int, db: Session = Depends(get_db)):
    """
    Synchronize note links based on wiki-style [[links]] in content.

    This scans the note content for [[Title]] patterns and automatically
    creates/removes links to match.
    """
    note = crud_note.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    crud_link.sync_note_links(db, note_id, note.content)
    return {"message": "Links synchronized successfully"}
