"""
Database connection and session management for PostgreSQL + pgvector.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from typing import Generator

from app.core.config import settings

# Create PostgreSQL engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Enable connection health checks
    pool_size=5,  # Number of connections to keep open
    max_overflow=10,  # Max additional connections when pool is exhausted
    echo=False,  # Set to True for SQL debugging
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
    Initialize database by creating pgvector extension and all tables.
    Should be called on application startup.
    """
    from app.db import models  # Import models to register them

    # Create pgvector extension (requires superuser or extension creation privileges)
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()
            print("pgvector extension created or already exists")
    except Exception as e:
        print(f"Warning: Could not create pgvector extension: {e}")
        print("Please ensure pgvector is installed on your PostgreSQL server")
        print("Run: CREATE EXTENSION IF NOT EXISTS vector;")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Create default "Default" project if it doesn't exist
    db = SessionLocal()
    try:
        existing_project = db.query(models.Project).filter(
            models.Project.name == "默认"
        ).first()

        if not existing_project:
            default_project = models.Project(
                name="默认",
                description="默认项目，用于存放未分类的任务",
                color="#667eea",
                is_system=True  # Mark as system project - cannot be deleted or edited
            )
            db.add(default_project)
            db.commit()
            print("Created default 'Default' project")
    finally:
        db.close()
