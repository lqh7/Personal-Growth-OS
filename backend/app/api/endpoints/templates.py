"""
Template management API endpoints (Iteration 2).
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.schemas.template import Template, TemplateCreate, TemplateUpdate
from app.crud import crud_template

router = APIRouter()


@router.get("/", response_model=List[Template])
def list_templates(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all templates with optional filtering.

    - **skip**: Number of templates to skip (pagination)
    - **limit**: Maximum number of templates to return
    - **category**: Filter by category (e.g., '工作', '学习', '生活')
    """
    return crud_template.get_templates(db, skip=skip, limit=limit, category=category)


@router.get("/categories", response_model=List[str])
def list_template_categories(db: Session = Depends(get_db)):
    """Get all unique template categories."""
    return crud_template.get_template_categories(db)


@router.get("/{template_id}", response_model=Template)
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get a specific template by ID."""
    template = crud_template.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("/", response_model=Template, status_code=status.HTTP_201_CREATED)
def create_template(template: TemplateCreate, db: Session = Depends(get_db)):
    """
    Create a new note template.

    Template placeholders:
    - `{date}`: Current date (YYYY-MM-DD)
    - `{title}`: Will be replaced when creating note
    - `{time}`: Current time (HH:MM)
    """
    return crud_template.create_template(db, template)


@router.put("/{template_id}", response_model=Template)
def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing template."""
    updated_template = crud_template.update_template(db, template_id, template_update)
    if not updated_template:
        raise HTTPException(status_code=404, detail="Template not found")
    return updated_template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(template_id: int, db: Session = Depends(get_db)):
    """Delete a template."""
    success = crud_template.delete_template(db, template_id)
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")


@router.post("/{template_id}/render", response_model=dict)
def render_template(
    template_id: int,
    title: Optional[str] = Query(None, description="Title to use in template"),
    db: Session = Depends(get_db)
):
    """
    Render a template with placeholders replaced.

    Returns the rendered content ready to be used in a new note.
    """
    template = crud_template.get_template(db, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    # Replace placeholders
    content = template.content_template
    now = datetime.now()

    replacements = {
        "{date}": now.strftime("%Y-%m-%d"),
        "{time}": now.strftime("%H:%M"),
        "{title}": title or "未命名笔记",
    }

    for placeholder, value in replacements.items():
        content = content.replace(placeholder, value)

    return {
        "content": content,
        "template_name": template.name,
        "suggested_title": title or f"{template.name} - {now.strftime('%Y-%m-%d')}"
    }
