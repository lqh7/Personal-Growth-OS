"""
Project management API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.project import Project, ProjectCreate, ProjectUpdate
from app.crud import crud_project

router = APIRouter()


@router.get("/", response_model=List[Project])
def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List all projects.

    - **skip**: Number of projects to skip (pagination)
    - **limit**: Maximum number of projects to return
    """
    projects = crud_project.get_projects(db, skip=skip, limit=limit)
    return projects


@router.get("/{project_id}", response_model=Project)
def get_project(project_id: int, db: Session = Depends(get_db)):
    """Get a specific project by ID."""
    project = crud_project.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.post("/", response_model=Project, status_code=201)
def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """
    创建新项目。

    Raises:
        HTTPException 400: 如果项目名称已存在
    """
    try:
        return crud_project.create_project(db, project)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
):
    """
    更新现有项目。

    Raises:
        HTTPException 404: 如果项目不存在
        HTTPException 400: 如果新名称与其他项目重名
    """
    try:
        updated_project = crud_project.update_project(db, project_id, project_update)
        if not updated_project:
            raise HTTPException(status_code=404, detail="Project not found")
        return updated_project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    """
    删除项目。

    Raises:
        HTTPException 404: 如果项目不存在
        HTTPException 403: 如果尝试删除系统项目
    """
    try:
        success = crud_project.delete_project(db, project_id)
        if not success:
            raise HTTPException(status_code=404, detail="Project not found")
    except ValueError as e:
        raise HTTPException(status_code=403, detail=str(e))
