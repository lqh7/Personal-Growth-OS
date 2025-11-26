"""
Task Igniter Agent using Agno Framework.
任务启动仪式 - 基于Agno的AI Agent,支持AgentOS API格式

This agent provides task decomposition capabilities with:
1. Task analysis and title extraction
2. Task decomposition into subtasks
3. Knowledge retrieval from vector store (RAG)
4. Minimum viable task identification
"""

from typing import List, Dict, Any, Optional
import json
import httpx
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.function import Function

from app.core.config import settings
from app.core.llm_factory import get_chat_model_config


# ============================================================================
# Tool Definitions - Tools available to the agent
# ============================================================================

def search_knowledge_base(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Search the knowledge base for related notes using pgvector semantic search.

    Args:
        query: Search query text
        limit: Maximum number of results to return

    Returns:
        List of related notes with metadata
    """
    try:
        from app.services.vector_store import get_vector_store
        from app.db.database import SessionLocal
        from app.crud import crud_note

        db = SessionLocal()
        try:
            vector_store = get_vector_store()
            results = vector_store.search_similar_notes(db, query, n_results=limit)

            # Enrich results with note content
            enriched_results = []
            for result in results:
                note = crud_note.get_note(db, result["note_id"])
                if note:
                    enriched_results.append({
                        "note_id": note.id,
                        "title": note.title,
                        "content": note.content[:200] + "..." if len(note.content) > 200 else note.content,
                        "similarity_score": result["score"]
                    })

            return enriched_results
        finally:
            db.close()
    except Exception as e:
        print(f"Knowledge base search error: {e}")
        return []


def format_task_summary(
    main_title: str,
    main_description: str,
    subtasks: List[Dict[str, Any]],
    mvt_index: int
) -> str:
    """
    Format the task decomposition results into a summary string.

    Args:
        main_title: Main task title
        main_description: Main task description
        subtasks: List of subtask dictionaries
        mvt_index: Index of minimum viable task

    Returns:
        Formatted summary string
    """
    lines = [
        f"📝 主任务: {main_title}",
        f"📋 描述: {main_description}",
        "",
        "🔹 子任务列表:",
    ]

    for i, task in enumerate(subtasks):
        is_mvt = " ⭐ (最小可行任务)" if i == mvt_index else ""
        lines.append(f"{i + 1}. {task['title']}{is_mvt}")
        lines.append(f"   {task['description']}")
        lines.append(f"   优先级: {task.get('priority', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# Agent Creation
# ============================================================================

def create_task_igniter_agent(agent_id: str = "task-igniter") -> Agent:
    """
    Create and configure the Task Igniter Agno Agent.

    Args:
        agent_id: Unique identifier for the agent

    Returns:
        Configured Agno Agent instance
    """
    # Get LLM configuration from centralized factory
    llm_config = get_chat_model_config()

    # Create custom httpx AsyncClient with JWT token in Authorization header
    # This bypasses OpenAI SDK's token validation for Trend Micro RDSEC ONE API
    custom_client = httpx.AsyncClient(
        headers={
            "Authorization": f"Bearer {settings.OPENAI_API_KEY}"
        },
        timeout=60.0
    )

    # Create OpenAI model instance with custom http_client
    # Agno uses OpenAI-compatible API format
    model = OpenAIChat(
        id=llm_config.get("model", "gpt-4"),
        api_key="dummy-key-not-used",  # Dummy key to bypass SDK validation
        base_url=getattr(settings, "OPENAI_API_BASE", None),
        http_client=custom_client
    )

    # Define agent instructions (system prompt)
    instructions = """你是一个任务分解专家助手，帮助用户将模糊的大任务分解为清晰的可执行子任务。

你的工作流程：
1. 分析用户输入，提炼出主任务的标题和描述
2. 将主任务分解为3-5个具体可执行的子任务
3. 识别最容易开始的"最小可行任务"(Minimum Viable Task)
4. 可选：从知识库检索相关笔记

分解原则：
- 每个子任务要具体、可执行、有明确的完成标准
- 第一个子任务应该是最容易开始的（降低启动摩擦）
- 按逻辑顺序排列子任务
- 每个子任务标题15-30字，描述50字以内

输出格式：
使用工具 `format_task_summary` 生成结构化的任务分解结果。

知识检索：
如果用户任务涉及技术或复杂主题，使用 `search_knowledge_base` 工具检索相关笔记。
"""

    # Create agent with tools (using correct Agno parameter names)
    agent = Agent(
        id=agent_id,  # Correct parameter name is 'id', not 'agent_id'
        name="Task Igniter Agent",
        model=model,
        instructions=instructions,
        tools=[search_knowledge_base, format_task_summary],  # Pass function references directly
        markdown=True,  # Enable markdown rendering
        stream_intermediate_steps=True,  # Show intermediate steps (equivalent to show_tool_calls)
        add_datetime_to_context=True,  # Add current datetime to context (correct parameter name)
    )

    return agent


# ============================================================================
# Convenience Functions
# ============================================================================

# Global agent instance (lazy initialization)
_agent_instance: Optional[Agent] = None


def get_task_igniter_agent() -> Agent:
    """
    Get or create the global Task Igniter Agent instance.

    Returns:
        Configured Agent instance
    """
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = create_task_igniter_agent()
    return _agent_instance


def decompose_task_sync(user_input: str, project_id: Optional[int] = None) -> str:
    """
    Synchronously decompose a task using the agent.

    Args:
        user_input: User's task description
        project_id: Optional project ID for context

    Returns:
        Agent's response as string
    """
    agent = get_task_igniter_agent()

    # Add project context if provided
    context = f"项目ID: {project_id}\n\n" if project_id else ""
    prompt = f"{context}{user_input}"

    # Run agent and get response
    response = agent.run(prompt, stream=False)

    # Extract content from response
    if hasattr(response, 'content'):
        return response.content
    return str(response)


async def decompose_task_async(user_input: str, project_id: Optional[int] = None) -> str:
    """
    Asynchronously decompose a task using the agent.

    Args:
        user_input: User's task description
        project_id: Optional project ID for context

    Returns:
        Agent's response as string
    """
    agent = get_task_igniter_agent()

    # Add project context if provided
    context = f"项目ID: {project_id}\n\n" if project_id else ""
    prompt = f"{context}{user_input}"

    # Run agent asynchronously
    response = await agent.arun(prompt, stream=False)

    # Extract content from response
    if hasattr(response, 'content'):
        return response.content
    return str(response)


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Test agent
    test_input = "准备项目演示PPT"

    print("🤖 Task Igniter Agent Test\n")
    print(f"Input: {test_input}\n")
    print("=" * 50)

    result = decompose_task_sync(test_input)
    print(result)
