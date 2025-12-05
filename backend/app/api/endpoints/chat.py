"""
Chat API endpoints with AgentOS compatibility.
Implements the AgentOS API format: /agents/{agent_id}/runs

Supports Server-Sent Events (SSE) streaming for real-time AI responses.
Uses LangGraph 1.0 framework for AI agents.
"""

from typing import Optional, AsyncIterator
import json
import time
import logging
from fastapi import APIRouter, Form, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import SystemMessage, HumanMessage

logger = logging.getLogger(__name__)

from app.agents.task_igniter_langgraph import get_task_igniter_agent
from app.agents.deep_researcher import create_deep_task_researcher
from app.agents.orchestrator import get_orchestrator
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
    agent_id: str,
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
        agent_id: The ID of the agent to run (task-igniter or deep-task-researcher)
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

    # ⭐ 选择 Agent
    # - task-igniter: 旧版任务分解 (单层架构)
    # - deep-task-researcher: 新版深度任务研究 (三层架构)
    # - orchestrator: 动态技能系统 (新架构)

    if agent_id == "orchestrator":
        # 使用动态技能 Orchestrator
        graph = get_orchestrator()
    elif agent_id == "deep-task-researcher":
        # 使用新的 Deep Task Researcher（三层架构）
        graph = create_deep_task_researcher()
    else:
        # Task Igniter (使用 create_react_agent，支持 streaming)
        graph = get_task_igniter_agent()

    # Prepare messages for THIS turn (not history - LangGraph handles that)
    # Note: create_react_agent uses state_modifier for system prompt,
    # so we only need to pass the user message
    context = f"项目ID: {project_id}\n\n" if project_id else ""
    user_message = f"{context}{message}"

    # Both agents now use the same message format
    messages = [HumanMessage(content=user_message)]

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
            if agent_id == "orchestrator":
                # Orchestrator 使用自己的状态结构
                input_state = {
                    "messages": messages,
                    "current_skill": None,
                    "skill_sop": None,
                    "available_tools": [],
                    "ui_commands": [],
                    "iteration_count": 0,
                }
            elif agent_id == "deep-task-researcher":
                # Deep Researcher 使用完整的 state 结构
                input_state = {
                    "messages": messages,
                    "needs_clarification": False,
                    "research_brief": None,
                    "supervisor_messages": [],
                    "notes": [],
                    "final_output": None
                }
            else:
                # Task Igniter (create_react_agent) 只需要 messages
                input_state = {"messages": messages}

            # ⭐ LangGraph 1.0: Use astream with stream_mode="messages" for token streaming
            chunk_count = 0
            logger.info(f"Starting astream with input_state keys: {input_state.keys()}")
            logger.info(f"Config: {config}")

            try:
                async for message, metadata in graph.astream(
                    input_state,
                    config=config,
                    stream_mode="messages"
                ):
                    chunk_count += 1
                    msg_type = getattr(message, "type", type(message).__name__)
                    msg_content = getattr(message, "content", None)
                    logger.info(f"Stream chunk {chunk_count}: type={msg_type}, content={repr(msg_content)[:50] if msg_content else None}")

                    # Handle message chunks (LLM token streaming)
                    # AIMessageChunk has type="AIMessageChunk" (for create_react_agent)
                    # Orchestrator returns type="ai" for full messages
                    if msg_content and msg_type in ("AIMessageChunk", "ai"):
                        logger.info(f"Yielding RunContent with content: {repr(msg_content)[:30]}")
                        yield _format_sse_chunk(RunResponseContent(
                            event=RunEvent.RUN_CONTENT,
                            content=msg_content,
                            content_type="text",
                            session_id=thread_id,
                            created_at=_get_timestamp(),
                        ))

                    # Handle tool calls if present
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tool_call in message.tool_calls:
                            tool_name = tool_call.get("name", "unknown")
                            yield _format_sse_chunk(RunResponseContent(
                                event=RunEvent.TOOL_CALL_STARTED,
                                content_type="tool",
                                event_data={
                                    "tool_name": tool_name,
                                    "tool_args": tool_call.get("args", {}),
                                },
                                session_id=thread_id,
                                created_at=_get_timestamp(),
                            ))

                            # Send UI refresh command after task/note tool calls
                            if tool_name.startswith("task_"):
                                yield _format_sse_chunk(RunResponseContent(
                                    event=RunEvent.UI_COMMAND,
                                    content_type="command",
                                    event_data={
                                        "type": "refresh",
                                        "payload": {"target": "tasks"}
                                    },
                                    session_id=thread_id,
                                    created_at=_get_timestamp(),
                                ))
                            elif tool_name.startswith("note_"):
                                yield _format_sse_chunk(RunResponseContent(
                                    event=RunEvent.UI_COMMAND,
                                    content_type="command",
                                    event_data={
                                        "type": "refresh",
                                        "payload": {"target": "notes"}
                                    },
                                    session_id=thread_id,
                                    created_at=_get_timestamp(),
                                ))

                logger.info(f"Streaming completed with {chunk_count} chunks")

                # ⭐ For orchestrator: Get final state and check for tool executions
                if agent_id == "orchestrator":
                    try:
                        final_state = await graph.aget_state(config)
                        if final_state and final_state.values:
                            messages_list = final_state.values.get("messages", [])
                            ui_commands = final_state.values.get("ui_commands", [])
                            logger.info(f"Final state: {len(messages_list)} messages, ui_commands={ui_commands}")

                            # Send UI commands from state
                            for cmd in ui_commands:
                                yield _format_sse_chunk(RunResponseContent(
                                    event=RunEvent.UI_COMMAND,
                                    content_type="command",
                                    event_data=cmd,
                                    session_id=thread_id,
                                    created_at=_get_timestamp(),
                                ))

                            # Check for ToolMessage to detect tool execution
                            from langchain_core.messages import ToolMessage
                            task_tool_executed = False
                            note_tool_executed = False

                            for msg in messages_list:
                                if isinstance(msg, ToolMessage):
                                    tool_name = getattr(msg, "name", "")
                                    if tool_name.startswith("task_"):
                                        task_tool_executed = True
                                    elif tool_name.startswith("note_"):
                                        note_tool_executed = True

                            # Send refresh commands if tools were executed
                            if task_tool_executed and not ui_commands:
                                logger.info("Task tool executed, sending refresh command")
                                yield _format_sse_chunk(RunResponseContent(
                                    event=RunEvent.UI_COMMAND,
                                    content_type="command",
                                    event_data={
                                        "type": "refresh",
                                        "payload": {"target": "tasks"}
                                    },
                                    session_id=thread_id,
                                    created_at=_get_timestamp(),
                                ))
                            if note_tool_executed and not ui_commands:
                                logger.info("Note tool executed, sending refresh command")
                                yield _format_sse_chunk(RunResponseContent(
                                    event=RunEvent.UI_COMMAND,
                                    content_type="command",
                                    event_data={
                                        "type": "refresh",
                                        "payload": {"target": "notes"}
                                    },
                                    session_id=thread_id,
                                    created_at=_get_timestamp(),
                                ))
                    except Exception as state_error:
                        logger.warning(f"Could not get final state: {state_error}")

            except Exception as stream_error:
                logger.error(f"Error during streaming: {stream_error}", exc_info=True)
                raise

        else:
            # ⭐ Non-streaming response with config
            if agent_id == "orchestrator":
                input_state = {
                    "messages": messages,
                    "current_skill": None,
                    "skill_sop": None,
                    "available_tools": [],
                    "ui_commands": [],
                    "iteration_count": 0,
                }
            elif agent_id == "deep-task-researcher":
                input_state = {
                    "messages": messages,
                    "needs_clarification": False,
                    "research_brief": None,
                    "supervisor_messages": [],
                    "notes": [],
                    "final_output": None
                }
            else:
                # Task Igniter (create_react_agent) 只需要 messages
                input_state = {"messages": messages}

            result = await graph.ainvoke(
                input_state,
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
        agent_id: The ID of the agent to run
                  - "task-igniter": 旧版任务分解 (单层架构)
                  - "deep-task-researcher": 新版深度任务研究 (三层架构)
        message: User input message
        stream: Whether to stream the response (default: True)
        user_id: Optional user identifier
        session_id: Optional session identifier (auto-generated if not provided)
        dependencies: Optional JSON string with additional parameters (e.g., {"task_id": 123})

    Returns:
        StreamingResponse with Server-Sent Events (SSE) format

    Example cURL:
        ```bash
        curl --location 'http://localhost:8000/api/chat/agents/deep-task-researcher/runs' \
            --header 'Content-Type: application/x-www-form-urlencoded' \
            --data-urlencode 'message=准备项目演示PPT' \
            --data-urlencode 'stream=True' \
            --data-urlencode 'user_id=user@example.com' \
            --data-urlencode 'session_id=session_123' \
            --data-urlencode 'dependencies={"task_id": 1}'
        ```
    """
    # Validate agent_id
    if agent_id not in ["task-igniter", "deep-task-researcher", "orchestrator"]:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found. Available agents: task-igniter, deep-task-researcher, orchestrator"
        )

    # Return streaming response
    return StreamingResponse(
        stream_agent_run(
            agent_id=agent_id,
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

    checkpointer = get_checkpointer()

    if not checkpointer:
        logger.warning("Checkpointer not initialized, returning empty session list")
        return SessionList(sessions=[], total=0, page=1, page_size=limit)

    try:
        # ⭐ List all checkpoints from LangGraph (async)
        checkpoints = []
        async for cp in checkpointer.alist({}):
            checkpoints.append(cp)

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
                    from datetime import datetime as dt
                    ts = int(dt.fromisoformat(ts).timestamp() * 1000)
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

    checkpointer = get_checkpointer()

    if not checkpointer:
        raise HTTPException(
            status_code=503,
            detail="Checkpointer not initialized"
        )

    try:
        # ⭐ Use checkpointer.aget_tuple() to get specific thread's latest state (async)
        config = {"configurable": {"thread_id": session_id}}
        checkpoint_tuple = await checkpointer.aget_tuple(config)

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
    LangGraph uses multiple tables: checkpoints, checkpoint_blobs, checkpoint_writes.

    Args:
        session_id: Session identifier (thread_id)

    Returns:
        Success response
    """
    from app.core.langgraph_checkpoint import _pool

    if _pool is None:
        raise HTTPException(
            status_code=503,
            detail="Checkpointer connection pool not initialized"
        )

    try:
        # ⭐ Use async connection pool to delete from all LangGraph tables
        # LangGraph's PostgresSaver creates multiple tables via setup():
        # - checkpoints: main checkpoint data
        # - checkpoint_blobs: binary data storage
        # - checkpoint_writes: write operations log
        total_deleted = 0

        async with _pool.connection() as conn:
            async with conn.cursor() as cur:
                # Delete from checkpoint_writes first (foreign key constraint)
                await cur.execute(
                    "DELETE FROM checkpoint_writes WHERE thread_id = %s",
                    (session_id,)
                )
                writes_deleted = cur.rowcount
                total_deleted += writes_deleted

                # Delete from checkpoint_blobs
                await cur.execute(
                    "DELETE FROM checkpoint_blobs WHERE thread_id = %s",
                    (session_id,)
                )
                blobs_deleted = cur.rowcount
                total_deleted += blobs_deleted

                # Delete from checkpoints (main table)
                await cur.execute(
                    "DELETE FROM checkpoints WHERE thread_id = %s",
                    (session_id,)
                )
                checkpoints_deleted = cur.rowcount
                total_deleted += checkpoints_deleted

            await conn.commit()

        if total_deleted == 0:
            raise HTTPException(
                status_code=404,
                detail=f"Session '{session_id}' not found"
            )

        logger.info(f"Deleted session {session_id}: checkpoints={checkpoints_deleted}, blobs={blobs_deleted}, writes={writes_deleted}")

        return {
            "message": f"Session '{session_id}' deleted successfully",
            "deleted_count": total_deleted
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}", exc_info=True)
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
                "description": "任务启动仪式 - 帮助分解模糊任务为可执行子任务 (LangGraph 1.0 单层架构)",
                "framework": "LangGraph 1.0",
                "capabilities": [
                    "任务分析",
                    "任务分解",
                    "最小可行任务识别"
                ]
            },
            {
                "id": "deep-task-researcher",
                "name": "Deep Task Researcher",
                "description": "深度任务研究员 - 基于知识库研究的智能任务分解 (LangGraph 1.0 三层架构)",
                "framework": "LangGraph 1.0",
                "capabilities": [
                    "用户意图澄清",
                    "知识库语义搜索",
                    "多层级研究委托",
                    "战略思考和反思",
                    "结构化任务分解",
                    "最小可行任务识别"
                ]
            },
            {
                "id": "orchestrator",
                "name": "Dynamic Skills Orchestrator",
                "description": "动态技能编排器 - 基于Markdown SOP的技能调度系统 (LangGraph 1.0 动态架构)",
                "framework": "LangGraph 1.0",
                "capabilities": [
                    "动态技能加载",
                    "意图识别和路由",
                    "任务CRUD操作",
                    "笔记搜索和管理",
                    "UI指令发送",
                    "多轮对话续做"
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
        "agents": ["task-igniter", "deep-task-researcher", "orchestrator"],
        "timestamp": _get_timestamp(),
    }


# ============================================================================
# WebSocket Endpoint for Real-time Chat
# ============================================================================

@router.websocket("/ws/agents/{agent_id}/chat")
async def websocket_agent_chat(
    websocket: WebSocket,
    agent_id: str
):
    """
    WebSocket endpoint for real-time agent chat.

    Replaces SSE for better bidirectional communication.

    Args:
        websocket: WebSocket connection
        agent_id: Agent ID (task-igniter or deep-task-researcher)

    Message Format (Client -> Server):
        {
            "type": "message",
            "content": "user message",
            "session_id": "optional_session_id",
            "dependencies": {"task_id": 123}  // optional
        }

    Message Format (Server -> Client):
        {
            "event": "RunStarted|RunContent|ToolCallStarted|RunCompleted|RunError",
            "content": "...",
            "session_id": "...",
            "created_at": 1234567890,
            ...
        }
    """
    await websocket.accept()

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_json()

            if data.get("type") != "message":
                await websocket.send_json({
                    "event": RunEvent.RUN_ERROR,
                    "content": f"Unknown message type: {data.get('type')}",
                    "created_at": _get_timestamp()
                })
                continue

            message = data.get("content", "")
            session_id = data.get("session_id")
            dependencies = data.get("dependencies")

            if not message:
                await websocket.send_json({
                    "event": RunEvent.RUN_ERROR,
                    "content": "Empty message content",
                    "created_at": _get_timestamp()
                })
                continue

            # Validate agent_id
            if agent_id not in ["task-igniter", "deep-task-researcher", "orchestrator"]:
                await websocket.send_json({
                    "event": RunEvent.RUN_ERROR,
                    "content": f"Agent '{agent_id}' not found. Available: task-igniter, deep-task-researcher, orchestrator",
                    "created_at": _get_timestamp()
                })
                continue

            # Run agent and stream results
            try:
                async for chunk_text in stream_agent_run(
                    agent_id=agent_id,
                    message=message,
                    stream=True,
                    user_id=None,
                    session_id=session_id,
                    dependencies=json.dumps(dependencies) if dependencies else None
                ):
                    # Parse the SSE chunk and send via WebSocket
                    try:
                        chunk_data = json.loads(chunk_text.strip())
                        await websocket.send_json(chunk_data)
                    except json.JSONDecodeError:
                        # Skip non-JSON chunks
                        pass

            except Exception as e:
                logger.error(f"WebSocket agent error: {str(e)}", exc_info=True)

                await websocket.send_json({
                    "event": RunEvent.RUN_ERROR,
                    "content": f"Agent error: {str(e)}",
                    "created_at": _get_timestamp()
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for agent {agent_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}", exc_info=True)
