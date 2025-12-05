"""
ToolFactory - Universal adapter for converting CRUD functions to LangChain Tools.

This module implements the "Hand" layer of the Brain-Hand separation architecture,
providing automatic wrapping of database operations as AI-callable tools.

Key Features:
- Automatic DB session injection and cleanup
- Unified error handling
- Preserves Pydantic schema structure for LLM tool calling
- Supports both sync and async execution
"""
import logging
from typing import Callable, Type, Optional, Any, Dict
from functools import wraps

from pydantic import BaseModel
from langchain_core.tools import BaseTool, StructuredTool

from app.db.database import get_db, SessionLocal

logger = logging.getLogger(__name__)


class ToolFactory:
    """
    Factory for converting CRUD functions to LangChain Tools.

    Automatically handles:
    - Database session lifecycle (get/close)
    - Error handling and logging
    - Pydantic schema preservation

    Example:
        >>> from app.crud import crud_task
        >>> from app.tools.schemas import TaskIdSchema
        >>>
        >>> task_get_tool = ToolFactory.from_crud(
        ...     func=crud_task.get_task,
        ...     name="task_get",
        ...     description="Get a task by its ID",
        ...     args_schema=TaskIdSchema
        ... )
    """

    @staticmethod
    def from_crud(
        func: Callable,
        name: str,
        description: str,
        args_schema: Optional[Type[BaseModel]] = None,
        return_direct: bool = False
    ) -> BaseTool:
        """
        Convert a CRUD function to a LangChain Tool.

        Args:
            func: The CRUD function to wrap. Must accept `db: Session` as first arg.
            name: Tool name for LLM invocation.
            description: Tool description for LLM context.
            args_schema: Pydantic schema for tool arguments.
            return_direct: If True, tool output is returned directly to user.

        Returns:
            A LangChain BaseTool instance.
        """

        def wrapped_func(**kwargs) -> str:
            """
            Wrapper that injects DB session and handles errors.
            """
            db = SessionLocal()
            try:
                # Call the original CRUD function with db session
                result = func(db, **kwargs)

                # Format result for LLM consumption
                if result is None:
                    return "Operation completed, but no data was returned."
                elif isinstance(result, bool):
                    return "Operation successful." if result else "Operation failed."
                elif isinstance(result, list):
                    if len(result) == 0:
                        return "No results found."
                    # Format list results
                    items = []
                    for item in result[:10]:  # Limit to 10 items
                        if hasattr(item, '__dict__'):
                            items.append(_format_model(item))
                        else:
                            items.append(str(item))
                    summary = f"Found {len(result)} items."
                    if len(result) > 10:
                        summary += f" Showing first 10."
                    return f"{summary}\n\n" + "\n---\n".join(items)
                elif hasattr(result, '__dict__'):
                    return _format_model(result)
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Tool {name} execution error: {e}", exc_info=True)
                return f"Error: {str(e)}"
            finally:
                db.close()

        # Create the tool with schema
        return StructuredTool.from_function(
            func=wrapped_func,
            name=name,
            description=description,
            args_schema=args_schema,
            return_direct=return_direct
        )

    @staticmethod
    def from_service(
        func: Callable,
        name: str,
        description: str,
        args_schema: Optional[Type[BaseModel]] = None,
        inject_db: bool = True,
        return_direct: bool = False
    ) -> BaseTool:
        """
        Convert a service function to a LangChain Tool.

        Similar to from_crud but with optional DB injection.
        Use for service functions that may or may not need DB session.

        Args:
            func: The service function to wrap.
            name: Tool name for LLM invocation.
            description: Tool description for LLM context.
            args_schema: Pydantic schema for tool arguments.
            inject_db: If True, inject DB session as first argument.
            return_direct: If True, tool output is returned directly to user.

        Returns:
            A LangChain BaseTool instance.
        """

        def wrapped_func(**kwargs) -> str:
            db = None
            try:
                if inject_db:
                    db = SessionLocal()
                    result = func(db, **kwargs)
                else:
                    result = func(**kwargs)

                # Format result
                if result is None:
                    return "Operation completed successfully."
                elif isinstance(result, dict):
                    return _format_dict(result)
                elif isinstance(result, list):
                    if len(result) == 0:
                        return "No results found."
                    items = [_format_dict(item) if isinstance(item, dict) else str(item)
                             for item in result[:10]]
                    return f"Found {len(result)} results:\n\n" + "\n---\n".join(items)
                else:
                    return str(result)

            except Exception as e:
                logger.error(f"Tool {name} execution error: {e}", exc_info=True)
                return f"Error: {str(e)}"
            finally:
                if db:
                    db.close()

        return StructuredTool.from_function(
            func=wrapped_func,
            name=name,
            description=description,
            args_schema=args_schema,
            return_direct=return_direct
        )


def _format_model(obj: Any) -> str:
    """
    Format a SQLAlchemy model or Pydantic model for LLM output.
    """
    if hasattr(obj, 'model_dump'):
        # Pydantic model
        data = obj.model_dump()
    elif hasattr(obj, '__dict__'):
        # SQLAlchemy model or regular object
        data = {k: v for k, v in obj.__dict__.items()
                if not k.startswith('_')}
    else:
        return str(obj)

    return _format_dict(data)


def _format_dict(data: Dict[str, Any]) -> str:
    """
    Format a dictionary for LLM output.
    """
    lines = []
    for key, value in data.items():
        if value is not None:
            # Format datetime objects
            if hasattr(value, 'isoformat'):
                value = value.isoformat()
            lines.append(f"- {key}: {value}")
    return "\n".join(lines)


# ============================================
# Tool Execution Helpers
# ============================================

def create_ui_command(cmd_type: str, **payload) -> dict:
    """
    Helper to create UI command dict for SSE streaming.

    Args:
        cmd_type: One of 'toast', 'refresh', 'navigate', 'modal'
        **payload: Command-specific payload data

    Returns:
        Dict suitable for UICommand schema

    Example:
        >>> create_ui_command("toast", message="Task created!", type="success")
        {'type': 'toast', 'payload': {'message': 'Task created!', 'type': 'success'}}

        >>> create_ui_command("refresh", target="tasks")
        {'type': 'refresh', 'payload': {'target': 'tasks'}}
    """
    return {
        "type": cmd_type,
        "payload": payload
    }
