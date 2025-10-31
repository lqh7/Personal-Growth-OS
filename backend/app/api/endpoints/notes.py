"""
Note management API endpoints with RAG integration.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.note import Note, NoteCreate, NoteUpdate, Tag, RelatedNote
from app.crud import crud_note
# Temporarily disabled AI features until chromadb dependencies are resolved
# from app.services.vector_store import get_vector_store

router = APIRouter()


# Temporarily disabled - requires chromadb dependency
# def vectorize_note_background(note_id: int, title: str, content: str, tags: List[str]):
#     """Background task to vectorize note and add to ChromaDB."""
#     vector_store = get_vector_store()
#     metadata = {
#         "title": title,
#         "tags": tags
#     }
#     vector_store.add_note(note_id, content, metadata)


@router.get("/", response_model=List[Note])
def list_notes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    List all notes with optional filtering.

    - **skip**: Number of notes to skip (pagination)
    - **limit**: Maximum number of notes to return
    - **project_id**: Filter by project ID
    """
    notes = crud_note.get_notes(db, skip=skip, limit=limit, project_id=project_id)
    return notes


@router.get("/{note_id}", response_model=Note)
def get_note(note_id: int, db: Session = Depends(get_db)):
    """Get a specific note by ID."""
    note = crud_note.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


@router.post("/", response_model=Note, status_code=201)
def create_note(
    note: NoteCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new note.

    Note: Automatic vectorization is temporarily disabled until chromadb dependencies are resolved.
    """
    db_note = crud_note.create_note(db, note)

    # Vectorization temporarily disabled
    # tag_names = [tag.name for tag in db_note.tags]
    # background_tasks.add_task(
    #     vectorize_note_background,
    #     db_note.id,
    #     db_note.title,
    #     db_note.content,
    #     tag_names
    # )

    return db_note


@router.put("/{note_id}", response_model=Note)
def update_note(
    note_id: int,
    note_update: NoteUpdate,
    db: Session = Depends(get_db)
):
    """
    Update an existing note.

    Note: Re-vectorization is temporarily disabled until chromadb dependencies are resolved.
    """
    updated_note = crud_note.update_note(db, note_id, note_update)
    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Re-vectorization temporarily disabled
    # if note_update.content is not None:
    #     tag_names = [tag.name for tag in updated_note.tags]
    #     background_tasks.add_task(
    #         vectorize_note_background,
    #         updated_note.id,
    #         updated_note.title,
    #         updated_note.content,
    #         tag_names
    #     )

    return updated_note


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    """
    Delete a note from the database.

    Note: Vector store deletion is temporarily disabled until chromadb dependencies are resolved.
    """
    success = crud_note.delete_note(db, note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Note not found")

    # Vector store deletion temporarily disabled
    # vector_store = get_vector_store()
    # vector_store.delete_note(note_id)


# Temporarily disabled - requires chromadb dependency
# @router.get("/search/semantic", response_model=List[RelatedNote])
# def search_notes_semantic(
#     query: str = Query(..., min_length=3),
#     limit: int = Query(5, ge=1, le=20),
#     db: Session = Depends(get_db)
# ):
#     """
#     Search notes using semantic search (RAG).
#
#     This endpoint performs similarity search in the vector store and returns
#     notes ranked by relevance to the query.
#
#     - **query**: Search query text
#     - **limit**: Maximum number of results
#     """
#     vector_store = get_vector_store()
#     results = vector_store.search_similar_notes(query, n_results=limit)
#
#     # Fetch full note objects from database
#     related_notes = []
#     for result in results:
#         note = crud_note.get_note(db, result["note_id"])
#         if note:
#             related_notes.append(
#                 RelatedNote(note=note, similarity_score=result["score"])
#             )
#
#     return related_notes


@router.get("/tags/", response_model=List[Tag])
def list_tags(db: Session = Depends(get_db)):
    """Get all available tags."""
    return crud_note.get_tags(db)


@router.get("/by-tag/{tag_name}", response_model=List[Note])
def get_notes_by_tag(tag_name: str, db: Session = Depends(get_db)):
    """Get all notes with a specific tag."""
    return crud_note.search_notes_by_tag(db, tag_name)
