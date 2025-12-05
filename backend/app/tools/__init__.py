"""
Tool Registry - Central registry for all AI-callable tools.

This module implements a declarative configuration for tools that can be
dynamically loaded by skills. Each tool is defined once and can be
referenced by multiple skills.

Usage:
    from app.tools import get_tools_by_names, TOOL_REGISTRY

    # Get specific tools for a skill
    tools = get_tools_by_names(["task_get", "task_create", "task_list"])
"""
from dataclasses import dataclass
from typing import Callable, Type, Optional, Dict, List

from pydantic import BaseModel
from langchain_core.tools import BaseTool

from app.tools.factory import ToolFactory
from app.tools.schemas import (
    TaskIdSchema,
    TaskListSchema,
    TaskCreateSchema,
    TaskUpdateSchema,
    TaskSnoozeSchema,
    NoteSearchSchema,
    NoteCreateSchema,
    NoteUpdateSchema,
    NoteIdSchema,
    NoteLinkCreateSchema,
    BacklinksSchema,
)

# Import CRUD modules
from app.crud import crud_task, crud_note


@dataclass
class ToolDef:
    """
    Tool definition for lazy loading.

    Attributes:
        func: The underlying function to wrap
        description: Human-readable description for LLM
        args_schema: Pydantic schema for arguments
        inject_db: Whether to inject DB session (default True for CRUD)
    """
    func: Callable
    description: str
    args_schema: Optional[Type[BaseModel]] = None
    inject_db: bool = True


# ============================================
# Wrapper Functions (adapt CRUD signatures)
# ============================================
# NOTE: These must be defined BEFORE TOOL_REGISTRY

def _create_task_wrapper(db, **kwargs):
    """Wrapper to adapt TaskCreateSchema to crud_task.create_task."""
    from app.schemas.task import TaskCreate
    task_data = TaskCreate(**kwargs)
    return crud_task.create_task(db, task_data)


def _update_task_wrapper(db, task_id: int, **kwargs):
    """Wrapper to adapt TaskUpdateSchema to crud_task.update_task."""
    from app.schemas.task import TaskUpdate
    # Remove task_id from kwargs as it's a separate parameter
    update_data = {k: v for k, v in kwargs.items() if v is not None}
    task_update = TaskUpdate(**update_data)
    return crud_task.update_task(db, task_id, task_update)


def _snooze_task_wrapper(db, task_id: int, snooze_until):
    """Wrapper to adapt TaskSnoozeSchema to crud_task.snooze_task."""
    return crud_task.snooze_task(db, task_id, snooze_until)


def _create_note_wrapper(db, **kwargs):
    """Wrapper to adapt NoteCreateSchema to crud_note.create_note."""
    from app.schemas.note import NoteCreate
    note_data = NoteCreate(**kwargs)
    return crud_note.create_note(db, note_data)


def _update_note_wrapper(db, note_id: int, **kwargs):
    """Wrapper to adapt NoteUpdateSchema to crud_note.update_note."""
    from app.schemas.note import NoteUpdate
    update_data = {k: v for k, v in kwargs.items() if v is not None}
    note_update = NoteUpdate(**update_data)
    return crud_note.update_note(db, note_id, note_update)


def _search_notes_wrapper(db, query: str, limit: int = 5):
    """Wrapper for semantic note search."""
    from app.services.vector_store import get_vector_store
    vector_store = get_vector_store()

    # Get search results (note_id, score)
    results = vector_store.search_similar_notes(db, query, n_results=limit)

    # Fetch full note data
    notes = []
    for result in results:
        note = crud_note.get_note(db, result["note_id"])
        if note:
            notes.append({
                "id": note.id,
                "title": note.title,
                "content": note.content[:200] + "..." if len(note.content) > 200 else note.content,
                "similarity_score": result["score"]
            })
    return notes


# ============================================
# Tool Registry - Declarative Configuration
# ============================================

TOOL_REGISTRY: Dict[str, ToolDef] = {
    # ----------------------------------------
    # Task Tools
    # ----------------------------------------
    "task_get": ToolDef(
        func=crud_task.get_task,
        description="Get a task by its ID. Returns task details including title, description, status, priority, and timestamps.",
        args_schema=TaskIdSchema,
    ),

    "task_list": ToolDef(
        func=crud_task.get_tasks,
        description="List tasks with optional filtering. Can filter by project_id and status. Returns paginated results.",
        args_schema=TaskListSchema,
    ),

    "task_create": ToolDef(
        func=_create_task_wrapper,
        description="Create a new task. Requires title. Optional: description, priority (1-5), project_id, due_date, start_time, end_time.",
        args_schema=TaskCreateSchema,
    ),

    "task_update": ToolDef(
        func=_update_task_wrapper,
        description="Update an existing task. Specify task_id and any fields to update: title, description, status, priority, due_date, etc.",
        args_schema=TaskUpdateSchema,
    ),

    "task_delete": ToolDef(
        func=crud_task.delete_task,
        description="Delete a task by its ID. This action is irreversible. Always confirm with user before deletion.",
        args_schema=TaskIdSchema,
    ),

    "task_snooze": ToolDef(
        func=_snooze_task_wrapper,
        description="Snooze a task until a specific time. The task will reappear after the snooze period ends.",
        args_schema=TaskSnoozeSchema,
    ),

    # ----------------------------------------
    # Note Tools
    # ----------------------------------------
    "note_get": ToolDef(
        func=crud_note.get_note,
        description="Get a note by its ID. Returns note content, tags, and metadata.",
        args_schema=NoteIdSchema,
    ),

    "note_search": ToolDef(
        func=_search_notes_wrapper,
        description="Semantic search for notes. Uses vector similarity to find notes related to the query.",
        args_schema=NoteSearchSchema,
    ),

    "note_create": ToolDef(
        func=_create_note_wrapper,
        description="Create a new note. Requires title and content (Markdown). Optional: tag_names, source_url.",
        args_schema=NoteCreateSchema,
    ),

    "note_update": ToolDef(
        func=_update_note_wrapper,
        description="Update an existing note. Specify note_id and any fields to update.",
        args_schema=NoteUpdateSchema,
    ),

    "note_delete": ToolDef(
        func=crud_note.delete_note,
        description="Delete a note by its ID. This action is irreversible.",
        args_schema=NoteIdSchema,
    ),
}


# ============================================
# Tool Loading Functions
# ============================================

# Cache for built tools
_tools_cache: Dict[str, BaseTool] = {}


def get_tool(name: str) -> BaseTool:
    """
    Get a single tool by name.

    Args:
        name: Tool name from TOOL_REGISTRY

    Returns:
        LangChain BaseTool instance

    Raises:
        KeyError: If tool name not found in registry
    """
    if name in _tools_cache:
        return _tools_cache[name]

    if name not in TOOL_REGISTRY:
        raise KeyError(f"Tool '{name}' not found in registry. Available: {list(TOOL_REGISTRY.keys())}")

    tool_def = TOOL_REGISTRY[name]
    tool = ToolFactory.from_crud(
        func=tool_def.func,
        name=name,
        description=tool_def.description,
        args_schema=tool_def.args_schema,
    )

    _tools_cache[name] = tool
    return tool


def get_tools_by_names(names: List[str]) -> List[BaseTool]:
    """
    Get multiple tools by their names.

    Args:
        names: List of tool names to load

    Returns:
        List of LangChain BaseTool instances

    Example:
        >>> tools = get_tools_by_names(["task_get", "task_create", "task_list"])
    """
    return [get_tool(name) for name in names]


def get_all_tool_names() -> List[str]:
    """Get list of all registered tool names."""
    return list(TOOL_REGISTRY.keys())


def get_tool_descriptions() -> Dict[str, str]:
    """Get dict of tool names to descriptions."""
    return {name: tool_def.description for name, tool_def in TOOL_REGISTRY.items()}


# ============================================
# Skill-Specific Tool Groups
# ============================================

# Pre-defined tool groups for common skills
SKILL_TOOL_GROUPS = {
    "task_manager": [
        "task_get",
        "task_list",
        "task_create",
        "task_update",
        "task_delete",
        "task_snooze",
    ],
    "note_manager": [
        "note_get",
        "note_search",
        "note_create",
        "note_update",
        "note_delete",
    ],
    "knowledge_search": [
        "note_search",
        "note_get",
    ],
}


def get_skill_tools(skill_name: str) -> List[BaseTool]:
    """
    Get all tools for a predefined skill group.

    Args:
        skill_name: Name of the skill group

    Returns:
        List of LangChain BaseTool instances
    """
    if skill_name not in SKILL_TOOL_GROUPS:
        raise KeyError(f"Skill '{skill_name}' not found. Available: {list(SKILL_TOOL_GROUPS.keys())}")

    return get_tools_by_names(SKILL_TOOL_GROUPS[skill_name])
