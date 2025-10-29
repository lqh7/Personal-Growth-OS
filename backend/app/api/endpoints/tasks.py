"""
Task management API endpoints.
"""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.task import (
    Task, TaskCreate, TaskUpdate,
    TaskIgnitionRequest, TaskIgnitionResponse
)
from app.crud import crud_task
from app.agents.task_igniter_agent import get_task_igniter
from app.services.vector_store import get_vector_store

router = APIRouter()


@router.get("/", response_model=List[Task])
def list_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    include_snoozed: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all tasks with optional filtering.

    - **skip**: Number of tasks to skip (pagination)
    - **limit**: Maximum number of tasks to return
    - **project_id**: Filter by project ID
    - **status**: Filter by status (pending/in_progress/completed/cancelled)
    - **include_snoozed**: Include tasks that are currently snoozed
    """
    tasks = crud_task.get_tasks(
        db,
        skip=skip,
        limit=limit,
        project_id=project_id,
        status=status,
        include_snoozed=include_snoozed
    )
    return tasks


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a specific task by ID."""
    task = crud_task.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/", response_model=Task, status_code=201)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    return crud_task.create_task(db, task)


@router.put("/{task_id}", response_model=Task)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing task."""
    updated_task = crud_task.update_task(db, task_id, task_update)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Task not found")
    return updated_task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    success = crud_task.delete_task(db, task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")


@router.post("/{task_id}/snooze", response_model=Task)
def snooze_task(
    task_id: int,
    snooze_until: datetime,
    db: Session = Depends(get_db)
):
    """
    Snooze a task until a specific time.
    The task will be hidden from the main view until the snooze time.
    """
    task = crud_task.snooze_task(db, task_id, snooze_until)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.post("/ignite", response_model=TaskIgnitionResponse)
def task_ignition_ritual(
    request: TaskIgnitionRequest,
    db: Session = Depends(get_db)
):
    """
    Task Ignition Ritual: Break down a large, vague task into actionable subtasks.

    This endpoint:
    1. Analyzes the user's task description
    2. Decomposes it into 3-5 concrete subtasks using AI
    3. Identifies the "minimum viable starting task"
    4. Searches for related notes from the knowledge base
    5. Creates the main task and all subtasks in the database

    This is a core feature of the "Action Initiator" pillar.
    """
    # Step 1: Use AI agent to decompose the task
    agent = get_task_igniter()
    decomposition = agent.decompose_task(request.task_description)

    # Step 2: Create main task in database
    main_task_data = TaskCreate(
        title=decomposition.main_task_title,
        description=decomposition.main_task_description,
        project_id=request.project_id,
        status="pending"
    )
    main_task = crud_task.create_task(db, main_task_data)

    # Step 3: Create subtasks
    subtasks = []
    minimum_viable_task = None

    for subtask_item in decomposition.subtasks:
        subtask_data = TaskCreate(
            title=subtask_item.title,
            description=subtask_item.description,
            priority=subtask_item.priority,
            parent_task_id=main_task.id,
            project_id=request.project_id,
            status="pending"
        )
        subtask = crud_task.create_task(db, subtask_data)
        subtasks.append(subtask)

        if subtask_item.is_minimum_viable:
            minimum_viable_task = subtask

    # Step 4: Search for related notes using RAG
    vector_store = get_vector_store()
    related_notes_results = vector_store.search_similar_notes(
        query=request.task_description,
        n_results=5
    )

    # Format related notes for response
    related_notes = [
        {
            "note_id": result["note_id"],
            "title": result["metadata"].get("title", "Untitled"),
            "similarity_score": result["score"]
        }
        for result in related_notes_results
        if result["score"] > 0.5  # Only include relevant matches
    ]

    return TaskIgnitionResponse(
        main_task=main_task,
        subtasks=subtasks,
        minimum_viable_task=minimum_viable_task or subtasks[0],
        related_notes=related_notes
    )
