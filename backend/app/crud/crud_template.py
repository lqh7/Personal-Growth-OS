"""
CRUD operations for NoteTemplate entity (Iteration 2).
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models import NoteTemplate
from app.schemas.template import TemplateCreate, TemplateUpdate


def get_templates(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None
) -> List[NoteTemplate]:
    """Get all templates with optional category filtering."""
    query = db.query(NoteTemplate)

    if category:
        query = query.filter(NoteTemplate.category == category)

    return query.order_by(NoteTemplate.created_at.desc()).offset(skip).limit(limit).all()


def get_template(db: Session, template_id: int) -> Optional[NoteTemplate]:
    """Get a specific template by ID."""
    return db.query(NoteTemplate).filter(NoteTemplate.id == template_id).first()


def create_template(db: Session, template: TemplateCreate) -> NoteTemplate:
    """Create a new template."""
    db_template = NoteTemplate(
        name=template.name,
        description=template.description,
        content_template=template.content_template,
        icon=template.icon,
        category=template.category
    )
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


def update_template(
    db: Session,
    template_id: int,
    template_update: TemplateUpdate
) -> Optional[NoteTemplate]:
    """Update an existing template."""
    db_template = get_template(db, template_id)
    if not db_template:
        return None

    update_data = template_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_template, key, value)

    db.commit()
    db.refresh(db_template)
    return db_template


def delete_template(db: Session, template_id: int) -> bool:
    """Delete a template."""
    db_template = get_template(db, template_id)
    if not db_template:
        return False

    db.delete(db_template)
    db.commit()
    return True


def get_template_categories(db: Session) -> List[str]:
    """Get all unique template categories."""
    results = db.query(NoteTemplate.category).distinct().filter(
        NoteTemplate.category.isnot(None)
    ).all()
    return [r[0] for r in results if r[0]]
