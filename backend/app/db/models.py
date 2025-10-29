"""
SQLAlchemy database models for Personal Growth OS.
Based on the three-pillar architecture design.
"""
from datetime import datetime
from typing import List
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, ForeignKey,
    Boolean, CheckConstraint, Table
)
from sqlalchemy.orm import relationship, Mapped, mapped_column

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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    tasks: Mapped[List["Task"]] = relationship("Task", back_populates="project")
    notes: Mapped[List["Note"]] = relationship("Note", back_populates="project")


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
        # CheckConstraint will be added separately for SQLite compatibility
    )
    priority: Mapped[int] = mapped_column(Integer, default=3)  # 1=highest, 5=lowest
    due_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    snooze_until: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="For flexible deferral feature - task resurfaces at this time"
    )
    parent_task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tasks.id"), nullable=True
    )
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    completed_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

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
            "status IN ('pending', 'in_progress', 'completed', 'cancelled')",
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
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="notes")
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
