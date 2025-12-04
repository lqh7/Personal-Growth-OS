"""
SQLAlchemy database models for Personal Growth OS.
Based on the three-pillar architecture design.
PostgreSQL + pgvector for unified data and vector storage.
"""
from datetime import datetime
from typing import List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Boolean, CheckConstraint, Table
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.db.database import Base


# Association table for many-to-many relationship between notes and tags
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", Integer, ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class Project(Base):
    """
    Project: Top-level organizational container.
    用于将不同领域的任务和笔记隔离开，方便聚焦。
    """
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    color: Mapped[str] = mapped_column(
        String(7),
        nullable=True,
        default="#667eea",
        comment="Project color identifier (hex color code)"
    )
    is_system: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        comment="System project flag - cannot be deleted or renamed"
    )
    # Uses local time to match frontend timezone (前端时间为准)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="project")


class Task(Base):
    """
    Task: Core entity for action management.
    任务管理的核心，支持状态管理和灵活的snooze功能。
    """
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        index=True,  # Indexed for filtering
        # CheckConstraint will be added separately for SQLite compatibility
    )
    priority: Mapped[int] = mapped_column(Integer, default=3, index=True)  # 1=highest, 5=lowest (indexed for sorting)
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    start_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Schedule start time - when the task is planned to begin"
    )
    end_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Schedule end time - when the task is planned to finish (optional)"
    )
    snooze_until: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="For flexible deferral feature - task resurfaces at this time"
    )
    last_reminder_sent_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Last time a start reminder was sent for this task (防止重复提醒)"
    )
    last_end_reminder_sent_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="Last time an end reminder was sent for this task (防止重复提醒)"
    )
    parent_task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True, index=True  # Indexed for filtering
    )
    # Uses local time to match frontend timezone (前端时间为准)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    completion_notes: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        comment="User's reflection notes when completing the task"
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="tasks")
    parent_task: Mapped["Task"] = relationship(
        "Task", remote_side=[id], back_populates="subtasks"
    )
    subtasks: Mapped[List["Task"]] = relationship(
        "Task", back_populates="parent_task", cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'overdue')",
            name="check_task_status"
        ),
    )


class Note(Base):
    """
    Note: Knowledge storage entity.
    知识的核心存储，支持RAG和可追溯性。
    """
    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Full note content for RAG and vectorization"
    )
    source_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=True,
        comment="Source URL for traceability - critical for trust"
    )

    # Iteration 1: Core enhancements
    cover_image: Mapped[str] = mapped_column(
        String(2048),
        nullable=True,
        comment="Cover image URL (can be local file path or external URL)"
    )
    emoji: Mapped[str] = mapped_column(
        String(10),
        nullable=True,
        comment="Emoji icon for the note (e.g., 📝)"
    )
    is_pinned: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        comment="Whether the note is pinned to top"
    )
    is_favorited: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        index=True,
        comment="Whether the note is favorited"
    )
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Number of times the note has been viewed"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Custom sort order weight for manual sorting"
    )

    # Uses local time to match frontend timezone (前端时间为准)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )

    # Relationships
    tags: Mapped[List["Tag"]] = relationship(
        "Tag", secondary=note_tags, back_populates="notes"
    )


class Tag(Base):
    """
    Tag: Knowledge connector for organizing notes.
    标签系统，通过多对多关系连接笔记。
    """
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    color: Mapped[str] = mapped_column(String(7), nullable=True)  # Hex color code
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    notes: Mapped[List["Note"]] = relationship(
        "Note", secondary=note_tags, back_populates="tags"
    )


class UserProfileMemory(Base):
    """
    User Profile Memory: AI assistant's understanding of user preferences.
    独立于业务数据，专门用于存储助手对用户的"认知"。
    """
    __tablename__ = "user_profile_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    memory_key: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        comment="Unique key for this memory item (e.g., 'preferred_work_time')"
    )
    memory_value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The actual memory content"
    )
    confidence_score: Mapped[float] = mapped_column(
        Integer,  # Store as percentage (0-100)
        default=100,
        comment="Confidence level of this memory (0-100)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="Soft delete flag - allows disabling without losing data"
    )
    # Uses local time to match frontend timezone (前端时间为准)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class NoteLink(Base):
    """
    Note Link: Bidirectional links between notes (Iteration 3).
    笔记双向链接，支持Wiki风格的知识网络。
    """
    __tablename__ = "note_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    source_note_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Source note that contains the link"
    )
    target_note_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Target note being linked to"
    )
    link_type: Mapped[str] = mapped_column(
        String(50),
        default="wiki",
        index=True,
        comment="Link type (wiki, reference, etc.)"
    )
    # Uses local time to match frontend timezone (前端时间为准)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="When the link was created"
    )


class NoteEmbedding(Base):
    """
    Note Embedding: Vector storage for semantic search using pgvector.
    笔记向量存储，用于语义搜索。使用 PostgreSQL pgvector 扩展。
    """
    __tablename__ = "note_embeddings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    note_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # Each note has only one embedding
        index=True,
        comment="Reference to the note being embedded"
    )
    chunk_index: Mapped[int] = mapped_column(
        Integer,
        default=0,
        comment="Chunk index for large notes (reserved for future use)"
    )
    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=True,
        comment="SHA-256 hash of content to detect changes"
    )
    # 384-dimensional vector for all-MiniLM-L6-v2 model
    embedding = mapped_column(
        Vector(384),
        nullable=False,
        comment="384-dimensional embedding vector from sentence-transformers"
    )
    # Uses local time to match frontend timezone (前端时间为准)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="When the embedding was created"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="When the embedding was last updated"
    )

    # Relationship
    note: Mapped["Note"] = relationship("Note")
