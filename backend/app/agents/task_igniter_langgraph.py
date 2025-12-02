"""
Task Igniter Agent using LangGraph 1.0 Framework.
任务启动仪式 - 基于LangGraph的AI Agent

This agent provides task decomposition capabilities:
1. Task analysis and title extraction
2. Task decomposition into subtasks
3. Minimum viable task identification

Migration from Agno to LangGraph 1.0 (2025-12-01)
"""

from typing import TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

from app.core.config import settings


# ============================================================================
# State Definition
# ============================================================================

class AgentState(TypedDict):
    """
    Agent state for task decomposition.

    Uses LangGraph's message-based state management with automatic message merging.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]


# ============================================================================
# LLM Creation
# ============================================================================

def create_llm():
    """
    Create LLM instance based on settings.LLM_PROVIDER.

    Supports:
    - openai: ChatOpenAI
    - claude: ChatAnthropic
    - ollama: ChatOllama

    Returns:
        LangChain ChatModel instance with streaming enabled
    """
    provider = settings.LLM_PROVIDER

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=getattr(settings, "OPENAI_API_BASE", None),
            streaming=True,
            temperature=0.7,
        )

    elif provider == "claude":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(
            model=settings.ANTHROPIC_MODEL,
            api_key=settings.ANTHROPIC_API_KEY,
            base_url=getattr(settings, "ANTHROPIC_API_BASE", None) if getattr(settings, "ANTHROPIC_API_BASE", None) else None,
            streaming=True,
            temperature=0.7,
        )

    elif provider == "ollama":
        from langchain_community.chat_models import ChatOllama
        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.7,
        )

    else:
        # Fallback to OpenAI
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            streaming=True,
            temperature=0.7,
        )


# ============================================================================
# Graph Nodes
# ============================================================================

def agent_node(state: AgentState) -> dict:
    """
    LLM reasoning node.

    Invokes the LLM with current conversation state and returns response.

    Args:
        state: Current agent state with message history

    Returns:
        Updated state with LLM response appended to messages
    """
    llm = create_llm()
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


# ============================================================================
# Graph Construction
# ============================================================================

def create_task_igniter_graph():
    """
    Create task igniter StateGraph using LangGraph 1.0 with PostgreSQL persistence.

    Graph structure:
    - Entry: agent_node (LLM reasoning)
    - Exit: END

    Persistence:
    - Uses PostgreSQL Checkpointer to save conversation history
    - Automatically loads previous messages when using the same thread_id

    Returns:
        Compiled StateGraph with checkpointer attached
    """
    # Import checkpointer (lazy import to avoid circular dependencies)
    from app.core.langgraph_checkpoint import get_checkpointer

    # System prompt (保持与 Agno 版本一致)
    system_prompt = """你是一个任务分解专家助手，帮助用户将模糊的大任务分解为清晰的可执行子任务。

你的工作流程：
1. 分析用户输入，提炼出主任务的标题和描述
2. 将主任务分解为3-5个具体可执行的子任务
3. 识别最容易开始的"最小可行任务"(Minimum Viable Task)

分解原则：
- 每个子任务要具体、可执行、有明确的完成标准
- 第一个子任务应该是最容易开始的（降低启动摩擦）
- 按逻辑顺序排列子任务
- 每个子任务标题15-30字，描述50字以内

输出格式：
使用清晰的Markdown格式输出分解结果，包含：
- 📝 主任务标题
- 📋 主任务描述
- 🔹 子任务列表（编号 + 标题 + 描述 + 优先级）
- ⭐ 标记最小可行任务（第一步最容易开始的）
"""

    # Create StateGraph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("agent", agent_node)

    # Define edges
    workflow.set_entry_point("agent")
    workflow.add_edge("agent", END)

    # ⭐ Compile graph with checkpointer for persistence
    checkpointer = get_checkpointer()
    if checkpointer:
        graph = workflow.compile(checkpointer=checkpointer)
    else:
        # Fallback: compile without checkpointer (in-memory only)
        graph = workflow.compile()

    # Store system prompt as graph metadata for later use
    graph.system_prompt = system_prompt

    return graph


# ============================================================================
# Public API - Global Instance
# ============================================================================

_graph_instance: Optional[StateGraph] = None


def get_task_igniter_agent():
    """
    Get or create the global Task Igniter Graph instance.

    Lazy initialization pattern for efficiency.

    Returns:
        Compiled StateGraph instance
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

    # Prepare messages
    system_prompt = graph.system_prompt
    context = f"项目ID: {project_id}\n\n" if project_id else ""
    user_message = f"{context}{user_input}"

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_message)
    ]

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
