"""
Database connection and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.core.config import settings

# Create SQLite engine with UTF-8 encoding support
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={
        "check_same_thread": False,  # Needed for SQLite
        "timeout": 30,  # Increase timeout for better concurrency
    },
    echo=False,  # Disabled to avoid Windows console encoding issues with Chinese characters
    pool_pre_ping=True,  # Enable connection health checks
    # Note: SQLite uses UTF-8 by default, but we ensure JSON response encoding in FastAPI
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database session.

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database by creating all tables.
    Should be called on application startup.
    """
    from app.db import models  # Import models to register them
    Base.metadata.create_all(bind=engine)

    # Create default "Unassigned Tasks" project if it doesn't exist
    db = SessionLocal()
    try:
        existing_project = db.query(models.Project).filter(
            models.Project.name == "未分配任务"
        ).first()

        if not existing_project:
            default_project = models.Project(
                name="未分配任务",
                description="默认项目，用于存放未分类的任务",
                color="#999999"
            )
            db.add(default_project)
            db.commit()
            print("Created default 'Unassigned Tasks' project")
    finally:
        db.close()
