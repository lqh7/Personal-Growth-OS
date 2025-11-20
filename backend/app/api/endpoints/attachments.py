"""
Attachment management API endpoints (Iteration 2).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.attachment import Attachment, AttachmentCreate
from app.crud import crud_attachment, crud_note
from app.services import file_storage

router = APIRouter()


@router.post("/", response_model=Attachment, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    note_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a file attachment for a note.

    - **note_id**: The ID of the note to attach the file to
    - **file**: The file to upload (multipart/form-data)

    Restrictions:
    - Maximum file size: 50MB
    - Allowed file types: images, PDFs, Office documents, text files, archives
    """
    # Check if note exists
    note = crud_note.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Check file size
    if file.size and file.size > file_storage.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size is {file_storage.MAX_FILE_SIZE / (1024 * 1024)}MB"
        )

    # Check MIME type
    if not file_storage.is_allowed_file(file.content_type):
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file.content_type}' not allowed"
        )

    # Save file
    try:
        filepath, original_filename, filesize = await file_storage.save_upload_file(file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Create attachment record
    attachment_data = AttachmentCreate(
        note_id=note_id,
        filename=original_filename,
        filepath=filepath,
        filesize=filesize,
        mimetype=file.content_type
    )

    attachment = crud_attachment.create_attachment(db, attachment_data)
    return attachment


@router.get("/note/{note_id}", response_model=List[Attachment])
def get_note_attachments(note_id: int, db: Session = Depends(get_db)):
    """Get all attachments for a specific note."""
    # Check if note exists
    note = crud_note.get_note(db, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return crud_attachment.get_attachments_by_note(db, note_id)


@router.get("/{attachment_id}", response_model=Attachment)
def get_attachment_info(attachment_id: int, db: Session = Depends(get_db)):
    """Get attachment metadata by ID."""
    attachment = crud_attachment.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    return attachment


@router.get("/{attachment_id}/download")
def download_attachment(attachment_id: int, db: Session = Depends(get_db)):
    """Download an attachment file."""
    attachment = crud_attachment.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Get full file path
    full_path = file_storage.get_full_path(attachment.filepath)

    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=str(full_path),
        media_type=attachment.mimetype,
        filename=attachment.filename
    )


@router.delete("/{attachment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attachment(attachment_id: int, db: Session = Depends(get_db)):
    """Delete an attachment and its file."""
    attachment = crud_attachment.get_attachment(db, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Delete file from storage
    file_storage.delete_upload_file(attachment.filepath)

    # Delete database record
    crud_attachment.delete_attachment(db, attachment_id)
