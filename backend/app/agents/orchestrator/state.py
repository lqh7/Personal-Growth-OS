"""
State definitions for the Orchestrator agent.

This module defines the TypedDict state that flows through the LangGraph orchestrator,
including message history, skill context, and UI commands.
"""
from typing import TypedDict, Optional, List, Annotated, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field


class OrchestratorState(TypedDict):
    """
    State definition for the Orchestrator graph.

    Attributes:
        messages: Conversation history with add_messages reducer
        current_skill: Name of the currently active skill (None if idle)
        skill_sop: The SOP content to inject (set by loader_node)
        available_tools: List of tool names available to the specialist
        ui_commands: Queue of UI commands to send to frontend
        iteration_count: Counter for multi-round execution
    """
    # Core conversation state
    messages: Annotated[List[BaseMessage], add_messages]

    # Skill context
    current_skill: Optional[str]
    skill_sop: Optional[str]
    available_tools: List[str]

    # UI command queue
    ui_commands: List[dict]

    # Execution control
    iteration_count: int


# ============================================
# Router Decision Models
# ============================================

class SkillActivation(BaseModel):
    """Model for router's skill activation decision."""
    should_activate: bool = Field(
        ...,
        description="Whether to activate a skill for this request"
    )
    skill_name: Optional[str] = Field(
        None,
        description="Name of the skill to activate (if should_activate is True)"
    )
    reason: str = Field(
        ...,
        description="Brief explanation of the routing decision"
    )


class ContinueDecision(BaseModel):
    """Model for continue_check node decision."""
    should_continue: bool = Field(
        ...,
        description="Whether there are more tasks to complete"
    )
    next_action: Optional[str] = Field(
        None,
        description="Description of the next action if continuing"
    )


# ============================================
# Sliding Window Helper
# ============================================

def apply_sliding_window(
    messages: List[BaseMessage],
    window_size: int = 10
) -> List[BaseMessage]:
    """
    Apply sliding window to message history.

    Preserves:
    - All system messages (always at the front)
    - Most recent `window_size` non-system messages

    This optimizes KV Cache usage while maintaining context.

    Args:
        messages: Full message history
        window_size: Maximum number of non-system messages to keep

    Returns:
        Trimmed message list
    """
    from langchain_core.messages import SystemMessage

    system_msgs = [m for m in messages if isinstance(m, SystemMessage)]
    other_msgs = [m for m in messages if not isinstance(m, SystemMessage)]

    # Keep most recent messages
    if len(other_msgs) > window_size:
        other_msgs = other_msgs[-window_size:]

    return system_msgs + other_msgs


def create_initial_state() -> OrchestratorState:
    """
    Create initial state for a new orchestrator session.

    Returns:
        Fresh OrchestratorState with default values
    """
    return OrchestratorState(
        messages=[],
        current_skill=None,
        skill_sop=None,
        available_tools=[],
        ui_commands=[],
        iteration_count=0,
    )
