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
    TaskIgnitionRequest, TaskIgnitionResponse,
    TaskListResponse, PaginationMeta
)
from app.crud import crud_task
# Temporarily disabled AI features until langgraph dependencies are resolved
# from app.agents.task_igniter_agent import get_task_igniter
# from app.services.vector_store import get_vector_store

router = APIRouter()


def calculate_task_status(task, now: datetime = None) -> str:
    """
    Calculate the correct status for a task based on current time and task times.

    Status Priority (from highest to lowest):
    1. completed - User marked as done (never auto-update)
    2. overdue - User manually marked (never auto-set, preserved from DB)
    3. archived - User archived (never auto-update)
    4. in_progress - Auto-calculated: start_time <= now < end_time
    5. pending - Auto-calculated: now < start_time OR no time set

    Note: We do NOT automatically set 'overdue'. This prevents confusion when users
    create tasks with past times or when tasks expire. Users should manually mark
    tasks as overdue if needed.

    Uses local time to match frontend's timezone (前端时间为准)
    """
    if now is None:
        now = datetime.now()

    # Priority 1: Never auto-change these user-controlled statuses
    if task.status in ['completed', 'overdue', 'archived']:
        return task.status

    # Priority 2: Auto-calculate in_progress
    # Task is in progress if: start_time <= now < end_time
    if task.start_time and now >= task.start_time:
        if task.end_time:
            # Has end_time: check if not yet expired
            if now < task.end_time:
                return 'in_progress'
            # If now >= end_time, keep current status (don't auto-set overdue)
            # User should manually mark as completed or overdue
        else:
            # No end_time: assume in progress once started
            return 'in_progress'

    # Priority 3: Auto-calculate pending
    # Task is pending if: now < start_time OR no start_time
    if task.start_time and now < task.start_time:
        return 'pending'

    # Default: return current status (for tasks without times)
    return task.status if task.status else 'pending'


# Temporarily disabled - requires langgraph dependency
# @router.get("/agent/visualization")
# def get_agent_visualization():
#     """
#     获取任务分解Agent的可视化图
#     返回Mermaid格式的图定义，可用于文档和debugging
#     """
#     agent = get_task_igniter()
#     mermaid_graph = agent.get_graph_visualization()
#
#     return {
#         "mermaid": mermaid_graph,
#         "message": "Use this Mermaid diagram to visualize the agent workflow"
#     }


@router.get("/", response_model=TaskListResponse)
def list_tasks(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(15, ge=1, le=100, description="Items per page"),
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    include_snoozed: bool = False,
    db: Session = Depends(get_db)
):
    """
    List all tasks with pagination and optional filtering.

    - **page**: Page number (1-indexed)
    - **page_size**: Number of items per page (default 15)
    - **project_id**: Filter by project ID
    - **status**: Filter by status (pending/in_progress/completed/overdue)
    - **include_snoozed**: Include tasks that are currently snoozed
    """
    # Calculate offset from page number
    skip = (page - 1) * page_size

    # Get total count for pagination
    total = crud_task.count_tasks(
        db,
        project_id=project_id,
        status=status,
        include_snoozed=include_snoozed
    )

    # Get paginated tasks
    tasks = crud_task.get_tasks(
        db,
        skip=skip,
        limit=page_size,
        project_id=project_id,
        status=status,
        include_snoozed=include_snoozed
    )

    # Auto-update task status based on current time, start_time, and end_time
    # Priority: completed > overdue > in_progress > pending
    now = datetime.now()
    for task in tasks:
        correct_status = calculate_task_status(task, now)
        if correct_status != task.status:
            task.status = correct_status
            db.commit()

    # Calculate total pages
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return TaskListResponse(
        items=tasks,
        pagination=PaginationMeta(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages
        )
    )


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
    created_task = crud_task.create_task(db, task)

    # Auto-calculate correct status based on current time (uses local time)
    now = datetime.now()
    correct_status = calculate_task_status(created_task, now)

    if correct_status != created_task.status:
        created_task.status = correct_status
        db.commit()
        db.refresh(created_task)

    return created_task


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


# Temporarily disabled - requires langgraph dependency
# @router.post("/ignite", response_model=TaskIgnitionResponse)
# def task_ignition_ritual(
#     request: TaskIgnitionRequest,
#     db: Session = Depends(get_db)
# ):
#     """
#     Task Ignition Ritual: Break down a large, vague task into actionable subtasks.
#
#     This endpoint:
#     1. Analyzes the user's task description
#     2. Decomposes it into 3-5 concrete subtasks using AI
#     3. Identifies the "minimum viable starting task"
#     4. Searches for related notes from the knowledge base
#     5. Creates the main task and all subtasks in the database
#
#     This is a core feature of the "Action Initiator" pillar.
#     """
#     # Step 1: Use LangGraph Agent to decompose the task
#     agent = get_task_igniter()
#     agent_state = agent.invoke(
#         user_input=request.task_description,
#         project_id=request.project_id
#     )
#
#     # Check if agent execution was successful
#     if agent_state["status"] == "error":
#         raise HTTPException(
#             status_code=500,
#             detail=f"Agent execution failed: {agent_state.get('error_message', 'Unknown error')}"
#         )
#
#     # Step 2: Create main task in database
#     main_task_data = TaskCreate(
#         title=agent_state["main_task_title"],
#         description=agent_state["main_task_description"],
#         project_id=request.project_id,
#         status="pending"
#     )
#     main_task = crud_task.create_task(db, main_task_data)
#
#     # Step 3: Create subtasks
#     subtasks = []
#     minimum_viable_task = None
#
#     for idx, subtask_item in enumerate(agent_state["subtasks"]):
#         subtask_data = TaskCreate(
#             title=subtask_item["title"],
#             description=subtask_item["description"],
#             priority=subtask_item.get("priority", 3),
#             parent_task_id=main_task.id,
#             project_id=request.project_id,
#             status="pending"
#         )
#         subtask = crud_task.create_task(db, subtask_data)
#         subtasks.append(subtask)
#
#         # Use the minimum_viable_task_index from agent state
#         if idx == agent_state["minimum_viable_task_index"]:
#             minimum_viable_task = subtask
#
#     # Step 4: Related notes already retrieved by agent
#     # Use the related_notes from agent state
#     related_notes = agent_state.get("related_notes", [])
#
#     return TaskIgnitionResponse(
#         main_task=main_task,
#         subtasks=subtasks,
#         minimum_viable_task=minimum_viable_task or subtasks[0],
#         related_notes=related_notes
#     )
