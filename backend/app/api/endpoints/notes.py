"""
Note management API endpoints with RAG integration using pgvector.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.schemas.note import Note, NoteCreate, NoteUpdate, Tag, RelatedNote, SearchHistory
from app.crud import crud_note
from app.services.vector_store import get_vector_store

router = APIRouter()


def vectorize_note_background(note_id: int, content: str):
    """
    Background task to vectorize note and add to pgvector.

    Args:
        note_id: ID of the note to vectorize
        content: Text content to embed
    """
    db = SessionLocal()
    try:
        vector_store = get_vector_store()
        vector_store.add_note(db, note_id, content)
    except Exception as e:
        print(f"Error vectorizing note {note_id}: {e}")
    finally:
        db.close()


@router.get("/", response_model=List[Note], response_model_exclude_unset=False, response_model_exclude_none=False)
def list_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all notes.

    - **skip**: Number of notes to skip (pagination)
    - **limit**: Maximum number of notes to return
    """
    notes = crud_note.get_notes(db, skip=skip, limit=limit)
    return notes


@router.get("/{note_id}", response_model=Note, response_model_exclude_unset=False, response_model_exclude_none=False)
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a specific note by ID."""
    note = crud_note.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("/", response_model=Note, status_code=201, response_model_exclude_unset=False, response_model_exclude_none=False)
def create_note(
    note: NoteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Create a new note.

    The note content will be automatically vectorized in the background
    for semantic search using pgvector.
    """
    db_note = crud_note.create_note(db, note)

    # Vectorize note in background
    background_tasks.add_task(
        vectorize_note_background,
        db_note.id,
        db_note.content
    )

    return db_note


@router.put("/{note_id}", response_model=Note)
def update_note(
    note_id: int,
    note_update: NoteUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Update an existing note.

    If content is updated, the note will be re-vectorized in the background.
    """
    updated_note = crud_note.update_note(db, note_id, note_update)
    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Re-vectorize if content was updated
    if note_update.content is not None:
        background_tasks.add_task(
            vectorize_note_background,
            updated_note.id,
            updated_note.content
        )

    return updated_note


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """
    Delete a note from the database.

    The note's vector embedding will also be deleted.
    """
    success = crud_note.delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")

    # Delete vector embedding
    vector_store = get_vector_store()
    vector_store.delete_note(db, note_id)


@router.get("/search/semantic", response_model=List[RelatedNote])
def search_notes_semantic(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Search notes using semantic similarity with pgvector.

    This endpoint performs vector-based semantic search to find notes
    that are conceptually similar to the query, even if they don't
    contain the exact words.

    - **query**: Search query text
    - **limit**: Maximum number of results
    """
    vector_store = get_vector_store()

    # Check if we have any embeddings
    embedding_count = vector_store.get_embedding_count(db)
    if embedding_count == 0:
        # Fallback to text search if no embeddings exist yet
        return _text_search_fallback(db, query, limit)

    # Perform semantic search
    search_results = vector_store.search_similar_notes(db, query, n_results=limit)

    # Fetch full note data for each result
    related_notes = []
    for result in search_results:
        note = crud_note.get_note(db, result["note_id"])
        if note:
            related_notes.append(
                RelatedNote(note=note, similarity_score=result["score"])
            )

    # Record search history
    crud_note.create_search_history(db, query, len(related_notes))

    return related_notes


def _text_search_fallback(db: Session, query: str, limit: int) -> List[RelatedNote]:
    """
    Fallback text-based search when no embeddings exist.

    Args:
        db: Database session
        query: Search query text
        limit: Maximum results

    Returns:
        List of related notes with dummy similarity scores
    """
    all_notes = crud_note.get_notes(db, skip=0, limit=1000)
    query_lower = query.lower()

    # Filter notes containing the query string
    matching_notes = [
        note for note in all_notes
        if query_lower in note.title.lower() or query_lower in note.content.lower()
    ]

    # Limit results
    matching_notes = matching_notes[:limit]

    # Record search history
    crud_note.create_search_history(db, query, len(matching_notes))

    # Convert to RelatedNote format (with dummy similarity score)
    return [
        RelatedNote(note=note, similarity_score=1.0)
        for note in matching_notes
    ]


@router.get("/tags/", response_model=List[Tag])
def list_tags(db: Session = Depends(get_db)):
    """Get all available tags."""
    return crud_note.get_tags(db)


@router.get("/by-tag/{tag_name}", response_model=List[Note])
def get_notes_by_tag(tag_name: str, db: Session = Depends(get_db)):
    """Get all notes with a specific tag."""
    return crud_note.search_notes_by_tag(db, tag_name)


# Iteration 1: Core enhancements

@router.put("/{note_id}/pin", response_model=Note)
def toggle_pin(
    note_id: int,
    pinned: bool = Query(..., description="Whether to pin the note"),
    db: Session = Depends(get_db)
):
    """Toggle note pinned status."""
    note = crud_note.toggle_note_pin(db, note_id, pinned)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.put("/{note_id}/favorite", response_model=Note)
def toggle_favorite(
    note_id: int,
    favorited: bool = Query(..., description="Whether to favorite the note"),
    db: Session = Depends(get_db)
):
    """Toggle note favorited status."""
    note = crud_note.toggle_note_favorite(db, note_id, favorited)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.get("/search/history", response_model=List[SearchHistory])
def get_search_history(
    limit: int = Query(10, ge=1, le=50, description="Number of recent searches to return"),
    db: Session = Depends(get_db)
):
    """Get recent search history."""
    return crud_note.get_search_history(db, limit=limit)
