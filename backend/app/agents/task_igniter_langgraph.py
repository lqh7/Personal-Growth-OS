"""
Task Igniter Agent using LangGraph 1.0 Framework.
任务启动仪式 - 基于LangGraph的AI Agent

This agent provides task decomposition capabilities:
1. Task analysis and title extraction
2. Task decomposition into subtasks
3. Minimum viable task identification

Migration from Agno to LangGraph 1.0 (2025-12-01)
Updated 2025-12-03: Use create_react_agent for proper streaming support
"""

from typing import Optional, Any
from langchain_core.messages import HumanMessage

from app.core.config import settings


# ============================================================================
# System Prompt
# ============================================================================

SYSTEM_PROMPT = """你是 Personal Growth OS 的 AI 助手，专注于帮助用户提升效率和个人成长。

你的主要能力：
1. **任务分解**: 当用户描述一个任务或目标时，帮助分解为可执行的子任务
2. **日常对话**: 友好地回应用户的问候和闲聊
3. **问题解答**: 回答关于任务管理、时间规划等问题

判断规则：
- 如果用户输入是问候（如"你好"、"hi"、"hello"等），友好地回应并询问如何帮助
- 如果用户描述了一个具体任务或目标，进行任务分解
- 如果不确定用户意图，礼貌地询问

任务分解格式（仅在需要时使用）：
📝 **主任务标题**
📋 主任务描述

🔹 **子任务列表**
1. 子任务标题 - 描述（优先级：高/中/低）⭐最小可行任务
2. 子任务标题 - 描述（优先级：高/中/低）
...

分解原则：
- 每个子任务具体、可执行、有明确完成标准
- 第一个子任务应最容易开始（降低启动摩擦）
- 3-5个子任务为宜
"""


# ============================================================================
# LLM Creation
# ============================================================================

def create_llm():
    """
    Create LLM instance based on settings.LLM_PROVIDER.

    Supports:
    - openai: ChatOpenAI (with JWT token support)
    - claude: ChatAnthropic
    - ollama: ChatOllama

    Returns:
        LangChain ChatModel instance with streaming enabled

    Note:
        For OpenAI provider, automatically detects JWT tokens and uses
        Authorization header for proxy services (e.g., TrendMicro).
    """
    # Use centralized utility function with JWT auth support
    from app.core.llm_utils import get_langchain_llm_with_auth
    return get_langchain_llm_with_auth()


# ============================================================================
# Graph Construction using create_react_agent
# ============================================================================

def create_task_igniter_graph():
    """
    Create task igniter agent using LangGraph 1.0's create_react_agent.

    Uses create_react_agent for proper streaming support with astream_events.
    The agent uses a system prompt for task decomposition guidance.

    Persistence:
    - Uses PostgreSQL Checkpointer to save conversation history
    - Automatically loads previous messages when using the same thread_id

    Returns:
        Compiled agent graph with checkpointer attached
    """
    import logging
    logger = logging.getLogger(__name__)

    # Import checkpointer (lazy import to avoid circular dependencies)
    from app.core.langgraph_checkpoint import get_checkpointer
    from langgraph.prebuilt import create_react_agent

    # Create LLM with streaming enabled
    llm = create_llm()
    logger.info(f"Created LLM: {llm.model_name}, streaming={llm.streaming}")

    # ⭐ Use create_react_agent for proper streaming support
    # No tools needed for simple task decomposition
    checkpointer = get_checkpointer()
    logger.info(f"Got checkpointer: {checkpointer is not None}")

    # Create agent with system prompt (LangGraph 1.0.3 API)
    graph = create_react_agent(
        model=llm,
        tools=[],  # No tools for basic task decomposition
        checkpointer=checkpointer,
        prompt=SYSTEM_PROMPT,  # Pass as string, not SystemMessage
    )

    logger.info(f"Created react agent, graph type: {type(graph).__name__}")

    # Store system prompt as graph metadata for compatibility
    graph.system_prompt = SYSTEM_PROMPT

    return graph


# ============================================================================
# Public API - Global Instance
# ============================================================================

_graph_instance: Optional[Any] = None


def get_task_igniter_agent():
    """
    Get or create the global Task Igniter Graph instance.

    Lazy initialization pattern for efficiency.

    Returns:
        Compiled agent graph instance
    """
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = create_task_igniter_graph()
    return _graph_instance


# ============================================================================
# Public API - Compatibility Functions
# ============================================================================

async def decompose_task_async(user_input: str, project_id: Optional[int] = None) -> str:
    """
    Asynchronously decompose a task using the agent.

    Provides compatibility with Agno version's API.

    Args:
        user_input: User's task description
        project_id: Optional project ID for context

    Returns:
        Agent's response as string
    """
    graph = get_task_igniter_agent()

    # Prepare messages (system prompt is already in state_modifier)
    context = f"项目ID: {project_id}\n\n" if project_id else ""
    user_message = f"{context}{user_input}"

    messages = [HumanMessage(content=user_message)]

    # Invoke graph (non-streaming for simple response)
    result = await graph.ainvoke({"messages": messages})

    # Extract content from last message
    if result and "messages" in result:
        last_message = result["messages"][-1]
        return last_message.content

    return ""


def decompose_task_sync(user_input: str, project_id: Optional[int] = None) -> str:
    """
    Synchronously decompose a task using the agent.

    Note: This is a compatibility wrapper. LangGraph prefers async execution.

    Args:
        user_input: User's task description
        project_id: Optional project ID for context

    Returns:
        Agent's response as string
    """
    import asyncio

    # Run async function in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(decompose_task_async(user_input, project_id))


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Test agent
    import asyncio

    test_input = "准备项目演示PPT"

    print("🤖 Task Igniter Agent (LangGraph 1.0) Test\n")
    print(f"Input: {test_input}\n")
    print("=" * 50)

    result = asyncio.run(decompose_task_async(test_input))
    print(result)
