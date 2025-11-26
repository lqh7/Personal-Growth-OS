"""
Chat API endpoints with AgentOS compatibility.
Implements the AgentOS API format: /agents/{agent_id}/runs

Supports Server-Sent Events (SSE) streaming for real-time AI responses.
"""

from typing import Optional, AsyncIterator
import json
import time
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

# Temporarily wrap Agno agent import to prevent startup failures
try:
    from app.agents.task_igniter_agno import get_task_igniter_agent
    AGNO_AVAILABLE = True
except Exception as e:
    print(f"Warning: Agno agent not available: {e}")
    AGNO_AVAILABLE = False
    get_task_igniter_agent = None

from app.schemas.chat import (
    RunResponseContent,
    RunEvent,
    ChatMessage,
    SessionHistoryResponse,
    SessionList,
    SessionEntry,
)

router = APIRouter()


# ============================================================================
# AgentOS-Compatible Streaming Endpoint
# ============================================================================

async def stream_agent_run(
    message: str,
    stream: bool,
    user_id: Optional[str],
    session_id: Optional[str],
    dependencies: Optional[str],
) -> AsyncIterator[str]:
    """
    Stream agent run events in AgentOS format.

    Yields SSE-formatted JSON chunks compatible with agent-ui.

    Args:
        message: User input message
        stream: Whether to stream the response
        user_id: Optional user identifier
        session_id: Optional session identifier
        dependencies: Optional JSON string with additional parameters (e.g., {"task_id": 123})

    Yields:
        JSON-formatted SSE chunks
    """
    # Parse dependencies if provided
    deps = {}
    if dependencies:
        try:
            deps = json.loads(dependencies)
        except json.JSONDecodeError:
            pass

    task_id = deps.get("task_id")
    project_id = deps.get("project_id")

    # Generate session_id if not provided
    if not session_id:
        session_id = f"session_{int(time.time() * 1000)}"

    # Check if Agno agent is available
    if not AGNO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Agno agent is not available. This feature is currently disabled.")

    # Get agent instance
    agent = get_task_igniter_agent()

    try:
        # Send RunStarted event
        yield _format_sse_chunk(RunResponseContent(
            event=RunEvent.RUN_STARTED,
            content_type="text",
            session_id=session_id,
            created_at=_get_timestamp(),
        ))

        # Run agent with streaming
        if stream:
            # Stream responses
            async for chunk in agent.arun(message, stream=True):
                # Extract content from RunOutputEvent
                if hasattr(chunk, 'content') and chunk.content:
                    yield _format_sse_chunk(RunResponseContent(
                        event=RunEvent.RUN_CONTENT,
                        content=chunk.content,
                        content_type="text",
                        session_id=session_id,
                        created_at=_get_timestamp(),
                    ))

                # Handle tool calls if present
                if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                    for tool_call in chunk.tool_calls:
                        yield _format_sse_chunk(RunResponseContent(
                            event=RunEvent.TOOL_CALL_STARTED,
                            content_type="text",
                            session_id=session_id,
                            tool={
                                "role": "tool",
                                "tool_call_id": tool_call.get("id", ""),
                                "tool_name": tool_call.get("function", {}).get("name", ""),
                                "tool_args": tool_call.get("function", {}).get("arguments", {}),
                                "tool_call_error": False,
                                "metrics": {"time": 0},
                                "created_at": _get_timestamp(),
                            },
                            created_at=_get_timestamp(),
                        ))

        else:
            # Non-streaming response
            response = await agent.arun(message, stream=False)
            content = response.content if hasattr(response, 'content') else str(response)

            yield _format_sse_chunk(RunResponseContent(
                event=RunEvent.RUN_CONTENT,
                content=content,
                content_type="text",
                session_id=session_id,
                created_at=_get_timestamp(),
            ))

        # Send RunCompleted event
        yield _format_sse_chunk(RunResponseContent(
            event=RunEvent.RUN_COMPLETED,
            content_type="text",
            session_id=session_id,
            created_at=_get_timestamp(),
        ))

    except Exception as e:
        # Send error event
        yield _format_sse_chunk(RunResponseContent(
            event=RunEvent.RUN_ERROR,
            content=f"Agent error: {str(e)}",
            content_type="text",
            session_id=session_id,
            event_data={"error": str(e)},
            created_at=_get_timestamp(),
        ))


def _format_sse_chunk(chunk: RunResponseContent) -> str:
    """
    Format RunResponseContent as SSE chunk.

    Args:
        chunk: Response content object

    Returns:
        SSE-formatted string (JSON object)
    """
    # Convert to dict and serialize as JSON
    chunk_dict = chunk.model_dump(exclude_none=True)
    return json.dumps(chunk_dict) + "\n"


def _get_timestamp() -> int:
    """Get current timestamp in milliseconds."""
    return int(time.time() * 1000)


@router.post("/agents/{agent_id}/runs")
async def run_agent(
    agent_id: str,
    message: str = Form(...),
    stream: bool = Form(True),
    user_id: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None),
    dependencies: Optional[str] = Form(None),  # URL-encoded JSON string
):
    """
    Run an agent with streaming support (AgentOS API compatible).

    This endpoint follows the AgentOS API format used by agent-ui.

    Args:
        agent_id: The ID of the agent to run (e.g., "task-igniter")
        message: User input message
        stream: Whether to stream the response (default: True)
        user_id: Optional user identifier
        session_id: Optional session identifier (auto-generated if not provided)
        dependencies: Optional JSON string with additional parameters (e.g., {"task_id": 123})

    Returns:
        StreamingResponse with Server-Sent Events (SSE) format

    Example cURL:
        ```bash
        curl --location 'http://localhost:8000/api/chat/agents/task-igniter/runs' \
            --header 'Content-Type: application/x-www-form-urlencoded' \
            --data-urlencode 'message=准备项目演示PPT' \
            --data-urlencode 'stream=True' \
            --data-urlencode 'user_id=user@example.com' \
            --data-urlencode 'session_id=session_123' \
            --data-urlencode 'dependencies={"task_id": 1}'
        ```
    """
    # Validate agent_id (currently only task-igniter supported)
    if agent_id not in ["task-igniter"]:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found. Available agents: task-igniter"
        )

    # Return streaming response
    return StreamingResponse(
        stream_agent_run(
            message=message,
            stream=stream,
            user_id=user_id,
            session_id=session_id,
            dependencies=dependencies,
        ),
        media_type="text/plain",  # SSE uses text/plain
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


# ============================================================================
# Session Management Endpoints
# ============================================================================

@router.get("/sessions", response_model=SessionList)
async def get_sessions(
    agent_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
):
    """
    Get session history list.

    Args:
        agent_id: Optional filter by agent ID
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip

    Returns:
        List of sessions with pagination metadata
    """
    # TODO: Implement session storage in database
    # For now, return empty list
    return SessionList(
        sessions=[],
        total=0,
        page=offset // limit + 1,
        page_size=limit,
    )


@router.get("/sessions/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    """
    Get message history for a specific session.

    Args:
        session_id: Session identifier

    Returns:
        Session with full message history
    """
    # TODO: Implement session storage in database
    raise HTTPException(
        status_code=404,
        detail=f"Session '{session_id}' not found"
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and its message history.

    Args:
        session_id: Session identifier

    Returns:
        Success response
    """
    # TODO: Implement session deletion
    return {"message": f"Session '{session_id}' deleted successfully"}


# ============================================================================
# Agent Listing Endpoint
# ============================================================================

@router.get("/agents")
async def list_agents():
    """
    List available agents.

    Returns:
        List of agent metadata
    """
    return {
        "agents": [
            {
                "id": "task-igniter",
                "name": "Task Igniter Agent",
                "description": "任务启动仪式 - 帮助分解模糊任务为可执行子任务",
                "capabilities": [
                    "任务分析",
                    "任务分解",
                    "最小可行任务识别",
                    "知识库检索"
                ]
            }
        ]
    }


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get("/health")
async def health_check():
    """
    Health check endpoint for agent service.

    Returns:
        Service status
    """
    return {
        "status": "healthy",
        "service": "chat-api",
        "agents": ["task-igniter"],
        "timestamp": _get_timestamp(),
    }
