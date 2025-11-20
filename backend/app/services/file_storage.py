"""
File storage service for handling file uploads (Iteration 2).
"""
import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple
from fastapi import UploadFile

# Base upload directory (relative to backend root)
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "notes"


def ensure_upload_dir():
    """Ensure the upload directory exists."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def generate_unique_filename(original_filename: str) -> str:
    """Generate a unique filename while preserving the extension."""
    # Get file extension
    ext = Path(original_filename).suffix

    # Generate UUID-based filename
    unique_id = uuid.uuid4().hex
    return f"{unique_id}{ext}"


async def save_upload_file(file: UploadFile) -> Tuple[str, str, int]:
    """
    Save an uploaded file to storage.

    Returns:
        Tuple of (relative_filepath, original_filename, filesize)
    """
    ensure_upload_dir()

    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    filepath = UPLOAD_DIR / unique_filename

    # Save file
    with filepath.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Get file size
    filesize = filepath.stat().st_size

    # Return relative path from backend root
    relative_path = f"uploads/notes/{unique_filename}"

    return relative_path, file.filename, filesize


def delete_upload_file(filepath: str) -> bool:
    """
    Delete a file from storage.

    Args:
        filepath: Relative path from backend root (e.g., "uploads/notes/abc123.pdf")

    Returns:
        True if deleted, False if file not found
    """
    full_path = Path(__file__).parent.parent.parent / filepath

    if full_path.exists():
        full_path.unlink()
        return True
    return False


def get_full_path(filepath: str) -> Path:
    """
    Get the full filesystem path for a relative filepath.

    Args:
        filepath: Relative path from backend root

    Returns:
        Full Path object
    """
    return Path(__file__).parent.parent.parent / filepath


# File size limits (in bytes)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    # Images
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    # Documents
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",  # .pptx
    # Text
    "text/plain",
    "text/markdown",
    "text/csv",
    # Archives
    "application/zip",
    "application/x-rar-compressed",
    "application/x-7z-compressed",
    # Other
    "application/json",
}


def is_allowed_file(mimetype: str) -> bool:
    """Check if a MIME type is allowed."""
    return mimetype in ALLOWED_MIME_TYPES
