"""
Chat Pydantic Schemas

Request/Response models for chat API endpoints.
Aligned with frontend types in frontend/src/types/chat.ts
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class RunEvent(str, Enum):
    """Run event types from LangGraph Agent streaming"""
    # Agent Run Events
    RUN_STARTED = "RunStarted"
    RUN_CONTENT = "RunContent"
    RUN_COMPLETED = "RunCompleted"
    RUN_ERROR = "RunError"
    RUN_OUTPUT = "RunOutput"

    # Tool Call Events
    TOOL_CALL_STARTED = "ToolCallStarted"
    TOOL_CALL_COMPLETED = "ToolCallCompleted"

    # Reasoning Events
    REASONING_STARTED = "ReasoningStarted"
    REASONING_STEP = "ReasoningStep"
    REASONING_COMPLETED = "ReasoningCompleted"

    # Memory Events
    MEMORY_UPDATE_STARTED = "MemoryUpdateStarted"
    MEMORY_UPDATE_COMPLETED = "MemoryUpdateCompleted"

    # Control Events
    RUN_CANCELLED = "RunCancelled"
    RUN_PAUSED = "RunPaused"
    RUN_CONTINUED = "RunContinued"


# ============================================================================
# Tool Call Schemas
# ============================================================================

class ToolCallMetrics(BaseModel):
    """Tool execution metrics"""
    time: float = Field(..., description="Execution time in milliseconds")


class ToolCall(BaseModel):
    """Tool call information"""
    role: Literal["user", "tool", "system", "assistant"]
    content: Optional[str] = None
    tool_call_id: str
    tool_name: str
    tool_args: Dict[str, Any] = Field(default_factory=dict)
    tool_call_error: bool = False
    metrics: ToolCallMetrics
    created_at: int = Field(..., description="Timestamp in milliseconds")


# ============================================================================
# Reasoning Schemas
# ============================================================================

class ReasoningStep(BaseModel):
    """Agent reasoning step"""
    title: str
    action: Optional[str] = None
    result: str
    reasoning: str
    confidence: Optional[float] = None
    next_action: Optional[str] = None


class ReasoningMessage(BaseModel):
    """Reasoning message (alternative format)"""
    role: Literal["user", "tool", "system", "assistant"]
    content: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_call_error: Optional[bool] = None
    metrics: Optional[ToolCallMetrics] = None
    created_at: Optional[int] = None


# ============================================================================
# Reference Schemas (RAG)
# ============================================================================

class ReferenceMetadata(BaseModel):
    """Reference metadata"""
    chunk: int
    chunk_size: int
    note_id: Optional[int] = None
    note_title: Optional[str] = None


class Reference(BaseModel):
    """Single reference/citation"""
    content: str
    meta_data: ReferenceMetadata
    name: str = Field(..., description="Document name")


class ReferenceData(BaseModel):
    """Knowledge base reference data"""
    query: str
    references: List[Reference]
    time: Optional[float] = None


# ============================================================================
# Message Schemas
# ============================================================================

class MessageExtraData(BaseModel):
    """Extra data for message (reasoning, references, etc.)"""
    reasoning_steps: Optional[List[ReasoningStep]] = None
    reasoning_messages: Optional[List[ReasoningMessage]] = None
    references: Optional[List[ReferenceData]] = None


class ChatMessage(BaseModel):
    """Chat message structure"""
    role: Literal["user", "assistant", "system"]
    content: str
    streaming_error: Optional[bool] = None
    created_at: int
    task_id: Optional[int] = None
    tool_calls: Optional[List[ToolCall]] = None
    extra_data: Optional[MessageExtraData] = None

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "帮我分解这个任务",
                "created_at": 1700000000000,
                "task_id": 123
            }
        }


# ============================================================================
# Session Schemas
# ============================================================================

class SessionEntry(BaseModel):
    """Chat session entry"""
    session_id: str
    session_name: str
    created_at: int
    updated_at: Optional[int] = None
    message_count: Optional[int] = None


class SessionList(BaseModel):
    """Session list with pagination"""
    sessions: List[SessionEntry]
    total: int
    page: int = 1
    page_size: int = 20


# ============================================================================
# Streaming Response Schemas
# ============================================================================

class RunResponseContent(BaseModel):
    """Run response content from streaming API"""
    content: Optional[Any] = None
    content_type: str = "text"
    event: RunEvent
    event_data: Optional[Dict[str, Any]] = None
    messages: Optional[List[Dict[str, Any]]] = None
    metrics: Optional[Dict[str, Any]] = None
    model: Optional[str] = None
    run_id: Optional[str] = None
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    tool: Optional[ToolCall] = None
    tools: Optional[List[ToolCall]] = None
    created_at: int
    extra_data: Optional[MessageExtraData] = None

    class Config:
        use_enum_values = True  # Convert enum to string in JSON


# ============================================================================
# Request/Response Schemas
# ============================================================================

class ChatStreamRequest(BaseModel):
    """Chat stream request payload"""
    message: str = Field(..., min_length=1, max_length=5000)
    task_id: Optional[int] = None
    session_id: Optional[str] = None
    stream: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "message": "帮我分解这个任务：准备项目演示",
                "task_id": 123,
                "session_id": None,
                "stream": True
            }
        }


class SessionHistoryResponse(BaseModel):
    """Chat session history response"""
    session_id: str
    messages: List[ChatMessage]
    created_at: int
    updated_at: int


class ChatSessionCreate(BaseModel):
    """Create new chat session"""
    session_name: Optional[str] = None
    task_id: Optional[int] = None


class ChatSessionUpdate(BaseModel):
    """Update chat session"""
    session_name: Optional[str] = None
