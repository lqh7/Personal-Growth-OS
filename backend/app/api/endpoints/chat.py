"""
Chat API endpoints with AgentOS compatibility.
Implements the AgentOS API format: /agents/{agent_id}/runs

Supports Server-Sent Events (SSE) streaming for real-time AI responses.
Uses LangGraph 1.0 framework for AI agents.
"""

from typing import Optional, AsyncIterator
import json
import time
from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import SystemMessage, HumanMessage

from app.agents.task_igniter_langgraph import get_task_igniter_agent
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
    Stream agent run events using LangGraph in AgentOS format with persistence.

    Yields SSE-formatted JSON chunks compatible with agent-ui.

    Persistence:
    - session_id is used as thread_id for LangGraph Checkpointer
    - Agent automatically loads previous messages from the same thread
    - All messages are saved after each run

    Args:
        message: User input message
        stream: Whether to stream the response
        user_id: Optional user identifier
        session_id: Optional session identifier (used as thread_id)
        dependencies: Optional JSON string with additional parameters (e.g., {"task_id": 123})

    Yields:
        JSON-formatted SSE chunks
    """
    import uuid

    # Parse dependencies if provided
    deps = {}
    if dependencies:
        try:
            deps = json.loads(dependencies)
        except json.JSONDecodeError:
            pass

    task_id = deps.get("task_id")
    project_id = deps.get("project_id")

    # Generate thread_id if not provided (this acts as session_id)
    thread_id = session_id or f"thread_{uuid.uuid4().hex[:16]}"

    # Get LangGraph instance
    graph = get_task_igniter_agent()
    system_prompt = graph.system_prompt

    # Prepare messages for THIS turn (not history - LangGraph handles that)
    context = f"项目ID: {project_id}\n\n" if project_id else ""
    user_message = f"{context}{message}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]

    # ⭐ Config for LangGraph persistence
    config = {
        "configurable": {
            "thread_id": thread_id  # LangGraph uses this to save/load state
        }
    }

    try:
        # Send RunStarted event
        yield _format_sse_chunk(RunResponseContent(
            event=RunEvent.RUN_STARTED,
            content_type="text",
            session_id=thread_id,  # Return thread_id to frontend
            created_at=_get_timestamp(),
        ))

        if stream:
            # ⭐ Stream using LangGraph with config for persistence
            async for event in graph.astream_events(
                {"messages": messages},
                config=config,  # Pass config to enable checkpointing
                version="v2"
            ):
                # Handle on_chat_model_stream events (LLM token streaming)
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if hasattr(chunk, "content") and chunk.content:
                        yield _format_sse_chunk(RunResponseContent(
                            event=RunEvent.RUN_CONTENT,
                            content=chunk.content,
                            content_type="text",
                            session_id=thread_id,
                            created_at=_get_timestamp(),
                        ))

        else:
            # ⭐ Non-streaming response with config
            result = await graph.ainvoke(
                {"messages": messages},
                config=config  # Pass config to enable checkpointing
            )

            # Extract content from last message
            if result and "messages" in result:
                last_message = result["messages"][-1]
                content = last_message.content

                yield _format_sse_chunk(RunResponseContent(
                    event=RunEvent.RUN_CONTENT,
                    content=content,
                    content_type="text",
                    session_id=thread_id,
                    created_at=_get_timestamp(),
                ))

        # Send RunCompleted event
        yield _format_sse_chunk(RunResponseContent(
            event=RunEvent.RUN_COMPLETED,
            content_type="text",
            session_id=thread_id,
            created_at=_get_timestamp(),
        ))

    except Exception as e:
        # Send error event
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Agent streaming error: {str(e)}", exc_info=True)

        yield _format_sse_chunk(RunResponseContent(
            event=RunEvent.RUN_ERROR,
            content=f"Agent error: {str(e)}",
            content_type="text",
            session_id=thread_id,
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
    Uses LangGraph 1.0 framework for AI agents.

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
    Get session history list using LangGraph Checkpointer.

    Retrieves all conversation threads from PostgreSQL checkpoints.

    Args:
        agent_id: Optional filter by agent ID (currently unused)
        limit: Maximum number of sessions to return
        offset: Number of sessions to skip

    Returns:
        List of sessions with pagination metadata
    """
    from app.core.langgraph_checkpoint import get_checkpointer
    import logging

    logger = logging.getLogger(__name__)
    checkpointer = get_checkpointer()

    if not checkpointer:
        logger.warning("Checkpointer not initialized, returning empty session list")
        return SessionList(sessions=[], total=0, page=1, page_size=limit)

    try:
        # ⭐ List all checkpoints from LangGraph
        checkpoints = list(checkpointer.list({}))

        # Group by thread_id to get unique sessions
        thread_map = {}
        for checkpoint_tuple in checkpoints:
            config = checkpoint_tuple.config
            thread_id = config.get("configurable", {}).get("thread_id")

            if not thread_id:
                continue

            # Keep only the latest checkpoint per thread
            if thread_id not in thread_map:
                thread_map[thread_id] = checkpoint_tuple

        # Convert to SessionEntry format
        sessions = []
        for thread_id, checkpoint_tuple in thread_map.items():
            try:
                # Extract state from checkpoint
                state = checkpoint_tuple.checkpoint.get("channel_values", {})
                messages = state.get("messages", [])

                # Get first user message as session name
                session_name = "新对话"
                for msg in messages:
                    if hasattr(msg, "type") and msg.type == "human":
                        session_name = msg.content[:50] if len(msg.content) > 50 else msg.content
                        break

                # Get timestamp (in milliseconds)
                ts = checkpoint_tuple.checkpoint.get("ts")
                if isinstance(ts, str):
                    # If ts is ISO timestamp string, convert to milliseconds
                    from datetime.datetime import fromisoformat
                    ts = int(fromisoformat(ts).timestamp() * 1000)
                elif not isinstance(ts, int):
                    ts = int(time.time() * 1000)

                sessions.append(SessionEntry(
                    session_id=thread_id,
                    session_name=session_name,
                    created_at=ts,
                    updated_at=ts,
                    message_count=len(messages)
                ))

            except Exception as e:
                logger.warning(f"Error processing session {thread_id}: {str(e)}")
                continue

        # Sort by created_at descending (newest first)
        sessions.sort(key=lambda x: x.created_at, reverse=True)

        # Apply pagination
        total = len(sessions)
        paginated_sessions = sessions[offset:offset+limit]

        return SessionList(
            sessions=paginated_sessions,
            total=total,
            page=offset // limit + 1,
            page_size=limit,
        )

    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}", exc_info=True)
        return SessionList(sessions=[], total=0, page=1, page_size=limit)


@router.get("/sessions/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    """
    Get message history for a specific session using LangGraph Checkpointer.

    Args:
        session_id: Session identifier (thread_id)

    Returns:
        Session with full message history
    """
    from app.core.langgraph_checkpoint import get_checkpointer
    import logging

    logger = logging.getLogger(__name__)
    checkpointer = get_checkpointer()

    if not checkpointer:
        raise HTTPException(
            status_code=503,
            detail="Checkpointer not initialized"
        )

    try:
        # ⭐ Use checkpointer.get_tuple() to get specific thread's latest state
        config = {"configurable": {"thread_id": session_id}}
        checkpoint_tuple = checkpointer.get_tuple(config)

        if not checkpoint_tuple:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found"
            )

        # Extract message history from checkpoint state
        state = checkpoint_tuple.checkpoint.get("channel_values", {})
        messages = state.get("messages", [])

        # Convert to ChatMessage format
        chat_messages = []
        for msg in messages:
            # Determine role based on message type
            role = "user" if hasattr(msg, "type") and msg.type == "human" else "assistant"

            chat_messages.append(ChatMessage(
                role=role,
                content=msg.content if hasattr(msg, "content") else str(msg),
                created_at=int(time.time() * 1000)  # Use current time as fallback
            ))

        # Get timestamp from checkpoint
        ts = checkpoint_tuple.checkpoint.get("ts")
        if isinstance(ts, str):
            # If ts is ISO timestamp string, convert to milliseconds
            from datetime import datetime
            ts = int(datetime.fromisoformat(ts).timestamp() * 1000)
        elif not isinstance(ts, int):
            ts = int(time.time() * 1000)

        return SessionHistoryResponse(
            session_id=session_id,
            messages=chat_messages,
            created_at=ts,
            updated_at=ts
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve session history: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session and its message history using LangGraph Checkpointer.

    This deletes all checkpoints associated with the given thread_id from PostgreSQL.

    Args:
        session_id: Session identifier (thread_id)

    Returns:
        Success response
    """
    from app.core.langgraph_checkpoint import get_checkpointer
    from app.db.database import get_db
    import logging

    logger = logging.getLogger(__name__)
    checkpointer = get_checkpointer()

    if not checkpointer:
        raise HTTPException(
            status_code=503,
            detail="Checkpointer not initialized"
        )

    try:
        # ⭐ Direct SQL deletion from checkpoints table
        # LangGraph's PostgresSaver doesn't have a built-in delete method,
        # so we need to delete directly from the database
        db = next(get_db())

        # Delete from checkpoints table (LangGraph's table)
        # The table structure is managed by LangGraph's setup()
        delete_query = """
        DELETE FROM checkpoints
        WHERE thread_id = :thread_id
        """

        result = db.execute(
            delete_query,
            {"thread_id": session_id}
        )
        db.commit()

        if result.rowcount == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found"
            )

        logger.info(f"Deleted session {session_id} ({result.rowcount} checkpoints)")

        return {
            "message": f"Session '{session_id}' deleted successfully",
            "deleted_count": result.rowcount
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


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
                "description": "任务启动仪式 - 帮助分解模糊任务为可执行子任务 (LangGraph 1.0)",
                "framework": "LangGraph 1.0",
                "capabilities": [
                    "任务分析",
                    "任务分解",
                    "最小可行任务识别"
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
