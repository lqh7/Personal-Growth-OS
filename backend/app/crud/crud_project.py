"""
CRUD operations for Project entity.
"""
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.models import Project
from app.schemas.project import ProjectCreate, ProjectUpdate


def get_project(db: Session, project_id: int) -> Optional[Project]:
    """Get a single project by ID."""
    return db.query(Project).filter(Project.id == project_id).first()


def get_projects(
    db: Session,
    skip: int = 0,
    limit: int = 100
) -> List[Project]:
    """
    Get list of all projects.

    Args:
        db: Database session
        skip: Number of records to skip (pagination)
        limit: Maximum number of records to return
    """
    return db.query(Project).offset(skip).limit(limit).all()


def get_project_by_name(db: Session, name: str, exclude_id: Optional[int] = None) -> Optional[Project]:
    """
    根据名称查询项目。

    Args:
        db: 数据库会话
        name: 项目名称
        exclude_id: 排除的项目ID(用于更新时排除自己)

    Returns:
        匹配的项目或None
    """
    query = db.query(Project).filter(Project.name == name)
    if exclude_id is not None:
        query = query.filter(Project.id != exclude_id)
    return query.first()


def create_project(db: Session, project: ProjectCreate) -> Project:
    """
    创建新项目。

    Args:
        db: 数据库会话
        project: 项目创建数据

    Returns:
        创建的项目

    Raises:
        ValueError: 如果项目名称已存在
    """
    # 检查名称是否已存在
    existing = get_project_by_name(db, project.name)
    if existing:
        raise ValueError(f"项目名称 '{project.name}' 已存在")

    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def update_project(db: Session, project_id: int, project_update: ProjectUpdate) -> Optional[Project]:
    """
    更新现有项目。

    Args:
        db: 数据库会话
        project_id: 项目ID
        project_update: 项目更新数据

    Returns:
        更新后的项目或None(如果项目不存在)

    Raises:
        ValueError: 如果新名称与其他项目重名，或尝试修改系统项目名称
    """
    db_project = get_project(db, project_id)
    if not db_project:
        return None

    update_data = project_update.model_dump(exclude_unset=True)

    # 系统项目保护：不允许修改名称
    if db_project.is_system and 'name' in update_data:
        raise ValueError("系统项目名称不可修改")

    # 如果更新包含名称,检查是否与其他项目重名
    if 'name' in update_data:
        existing = get_project_by_name(db, update_data['name'], exclude_id=project_id)
        if existing:
            raise ValueError(f"项目名称 '{update_data['name']}' 已存在")

    for field, value in update_data.items():
        setattr(db_project, field, value)

    db.commit()
    db.refresh(db_project)
    return db_project


def delete_project(db: Session, project_id: int) -> bool:
    """
    删除项目，并将该项目下的任务迁移到默认项目。

    Args:
        db: 数据库会话
        project_id: 项目ID

    Returns:
        True if successful, False if project not found

    Raises:
        ValueError: 如果尝试删除系统项目
    """
    from app.db.models import Task  # 导入Task模型

    db_project = get_project(db, project_id)
    if not db_project:
        return False

    # 系统项目保护：不允许删除
    if db_project.is_system:
        raise ValueError("系统项目不可删除")

    # 将该项目下的所有任务迁移到默认项目（ID=1）
    db.query(Task).filter(Task.project_id == project_id).update(
        {"project_id": 1},
        synchronize_session=False
    )

    db.delete(db_project)
    db.commit()
    return True
