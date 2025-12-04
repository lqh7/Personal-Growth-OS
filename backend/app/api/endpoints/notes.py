"""
Note management API endpoints with RAG integration using pgvector.
Supports both legacy vector_store and new llama-index implementation.
"""
import logging
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db, SessionLocal
from app.schemas.note import (
    Note, NoteCreate, NoteUpdate, Tag, RelatedNote,
    PaginatedNotes, BatchNoteIds, BatchPinRequest, BatchTagRequest
)
from app.crud import crud_note
from app.services.vector_store import get_vector_store

# Optional llama-index import
try:
    from app.services.llamaindex_service import get_llamaindex_service
    LLAMAINDEX_AVAILABLE = True
except ImportError:
    LLAMAINDEX_AVAILABLE = False

logger = logging.getLogger(__name__)
router = APIRouter()


def vectorize_note_background(note_id: int, title: str, content: str):
    """
    Background task to vectorize note and add to vector stores.
    Supports both legacy vector_store and llama-index.

    Args:
        note_id: ID of the note to vectorize
        title: Note title
        content: Text content to embed
    """
    db = SessionLocal()
    try:
        # Legacy vector_store
        vector_store = get_vector_store()
        vector_store.add_note(db, note_id, content)

        # LlamaIndex (if available)
        if LLAMAINDEX_AVAILABLE:
            try:
                llamaindex_service = get_llamaindex_service()
                llamaindex_service.add_note(db, note_id, title, content)
            except Exception as e:
                logger.warning(f"LlamaIndex vectorization failed for note {note_id}: {e}")

    except Exception as e:
        logger.error(f"Error vectorizing note {note_id}: {e}")
    finally:
        db.close()


@router.get("/", response_model=List[Note], response_model_exclude_unset=False, response_model_exclude_none=False)
def list_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all notes (legacy, for backward compatibility).

    - **skip**: Number of notes to skip (pagination)
    - **limit**: Maximum number of notes to return
    """
    notes = crud_note.get_notes(db, skip=skip, limit=limit)
    return notes


@router.get("/paginated", response_model=PaginatedNotes)
def list_notes_paginated(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    List notes with pagination metadata.

    Returns total count and page info for frontend pagination.
    """
    skip = (page - 1) * size
    notes = crud_note.get_notes(db, skip=skip, limit=size)
    total = crud_note.get_notes_count(db)
    pages = math.ceil(total / size) if total > 0 else 1

    return PaginatedNotes(
        items=notes,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


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
    for semantic search using pgvector and llama-index.
    """
    db_note = crud_note.create_note(db, note)

    # Vectorize note in background
    background_tasks.add_task(
        vectorize_note_background,
        db_note.id,
        db_note.title,
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

    If content or title is updated, the note will be re-vectorized in the background.
    """
    updated_note = crud_note.update_note(db, note_id, note_update)
    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Re-vectorize if content or title was updated
    if note_update.content is not None or note_update.title is not None:
        background_tasks.add_task(
            vectorize_note_background,
            updated_note.id,
            updated_note.title,
            updated_note.content
        )

    return updated_note


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """
    Delete a note from the database.

    The note's vector embedding will also be deleted from both stores.
    """
    success = crud_note.delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")

    # Delete vector embedding from legacy store
    vector_store = get_vector_store()
    vector_store.delete_note(db, note_id)

    # Delete from llama-index if available
    if LLAMAINDEX_AVAILABLE:
        try:
            llamaindex_service = get_llamaindex_service()
            llamaindex_service.delete_note(note_id)
        except Exception as e:
            logger.warning(f"Failed to delete note {note_id} from LlamaIndex: {e}")


@router.get("/search/debug")
def search_notes_debug(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Debug endpoint to test semantic search without response_model validation."""
    logger.debug(f"search_notes_debug called with query={query}, limit={limit}")
    try:
        vector_store = get_vector_store()
        embedding_count = vector_store.get_embedding_count(db)
        logger.debug(f"embedding_count={embedding_count}")

        if embedding_count == 0:
            return {"error": "no embeddings", "count": embedding_count}

        search_results = vector_store.search_similar_notes(db, query, n_results=limit)
        logger.debug(f"search_results count={len(search_results)}")

        results = []
        for result in search_results:
            note = crud_note.get_note(db, result["note_id"])
            if note:
                results.append({
                    "note_id": note.id,
                    "title": note.title,
                    "score": result["score"]
                })

        return {"results": results, "embedding_count": embedding_count}
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        logger.error(f"Debug search error: {e}")
        logger.error(tb)
        return {"error": str(e), "traceback": tb}


@router.get("/search/semantic", response_model=List[RelatedNote])
def search_notes_semantic(
    query: str = Query(..., min_length=1),
    limit: int = Query(5, ge=1, le=50),
    min_score: float = Query(0.3, ge=0.0, le=1.0, description="Minimum similarity score threshold"),
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
    logger.info(f"Semantic search: query={query}, limit={limit}")
    try:
        vector_store = get_vector_store()

        # Check if we have any embeddings
        embedding_count = vector_store.get_embedding_count(db)
        if embedding_count == 0:
            # Fallback to text search if no embeddings exist yet
            return _text_search_fallback(db, query, limit)

        # Perform semantic search
        search_results = vector_store.search_similar_notes(db, query, n_results=limit)

        # Fetch full note data for each result, filtering by min_score
        related_notes = []
        for result in search_results:
            # Skip results below the minimum score threshold
            if result["score"] < min_score:
                continue
            note = crud_note.get_note(db, result["note_id"])
            if note:
                related_notes.append(
                    RelatedNote(note=note, similarity_score=result["score"])
                )

        return related_notes
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


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


# ============================================
# Text Search API
# ============================================

@router.get("/search/text", response_model=List[Note])
def search_notes_text(
    query: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """
    Search notes using text matching (title and content).

    Unlike semantic search, this performs exact substring matching.
    Useful for finding notes with specific keywords.
    """
    notes = crud_note.search_notes_by_text(db, query, limit=limit)
    return notes


# ============================================
# Batch Operations API
# ============================================

@router.post("/batch/pin", response_model=List[Note])
def batch_pin_notes(
    request: BatchPinRequest,
    db: Session = Depends(get_db)
):
    """
    Batch pin or unpin multiple notes.

    - **note_ids**: List of note IDs to operate on
    - **pinned**: Whether to pin (True) or unpin (False)
    """
    updated_notes = []
    for note_id in request.note_ids:
        note = crud_note.toggle_note_pin(db, note_id, request.pinned)
        if note:
            updated_notes.append(note)
    return updated_notes


@router.post("/batch/favorite", response_model=List[Note])
def batch_favorite_notes(
    request: BatchPinRequest,
    db: Session = Depends(get_db)
):
    """
    Batch favorite or unfavorite multiple notes.

    Uses same schema as pin (pinned field is used for favorited).
    """
    updated_notes = []
    for note_id in request.note_ids:
        note = crud_note.toggle_note_favorite(db, note_id, request.pinned)
        if note:
            updated_notes.append(note)
    return updated_notes


@router.post("/batch/delete", status_code=200)
def batch_delete_notes(
    request: BatchNoteIds,
    db: Session = Depends(get_db)
):
    """
    Batch delete multiple notes.

    Returns the count of successfully deleted notes.
    """
    deleted_count = 0
    vector_store = get_vector_store()

    for note_id in request.note_ids:
        if crud_note.delete_note(db, note_id):
            # Delete vector embeddings
            vector_store.delete_note(db, note_id)
            if LLAMAINDEX_AVAILABLE:
                try:
                    llamaindex_service = get_llamaindex_service()
                    llamaindex_service.delete_note(note_id)
                except Exception:
                    pass
            deleted_count += 1

    return {"deleted": deleted_count, "total": len(request.note_ids)}


@router.post("/batch/tag", response_model=List[Note])
def batch_tag_notes(
    request: BatchTagRequest,
    db: Session = Depends(get_db)
):
    """
    Batch add tags to multiple notes.

    - **note_ids**: List of note IDs
    - **tag_names**: List of tag names to add
    - **mode**: 'add' to append tags, 'replace' to replace all tags
    """
    updated_notes = []
    for note_id in request.note_ids:
        note = crud_note.get_note(db, note_id)
        if note:
            if request.mode == "replace":
                new_tags = request.tag_names
            else:  # add mode
                existing_tag_names = [t.name for t in note.tags]
                new_tags = list(set(existing_tag_names + request.tag_names))

            # Use update to set tags
            from app.schemas.note import NoteUpdate
            update_data = NoteUpdate(tag_names=new_tags)
            updated_note = crud_note.update_note(db, note_id, update_data)
            if updated_note:
                updated_notes.append(updated_note)

    return updated_notes


# ============================================
# LlamaIndex Sync API (Admin)
# ============================================

@router.post("/admin/sync-vectors", status_code=200)
def sync_all_vectors(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Synchronize all notes to vector stores.

    This is an admin endpoint for rebuilding the vector index.
    Runs in the background.
    """
    from app.db.models import Note as NoteModel

    notes = db.query(NoteModel).all()
    note_count = len(notes)

    # Add background task for each note
    for note in notes:
        background_tasks.add_task(
            vectorize_note_background,
            note.id,
            note.title,
            note.content
        )

    return {
        "message": f"Started vectorization for {note_count} notes",
        "count": note_count
    }
