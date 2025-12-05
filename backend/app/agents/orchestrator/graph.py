"""
LangGraph Orchestrator - Dynamic skill-based agent system with keyword routing.

This module implements the main orchestrator graph that:
1. Routes user requests to appropriate skills (router_node)
2. Loads skill SOP via suffix injection (loader_node)
3. Executes specialist agent with skill-specific tools (specialist_node)
4. Handles multi-round continuation (continue_check)

Graph Structure:
    START --> router_node --> loader_node --> specialist_node --> continue_check --> END
                  |                                                   |
                  v                                                   v
             idle_response --> END                              (loop back to specialist)
"""
import logging
from typing import Literal, Optional

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END

from app.agents.orchestrator.state import (
    OrchestratorState,
    SkillActivation,
    ContinueDecision,
    apply_sliding_window,
)
from app.skills import get_skill_registry
from app.tools import get_tools_by_names
from app.core.llm_factory import get_langchain_llm
from app.core.langgraph_checkpoint import get_checkpointer

logger = logging.getLogger(__name__)

# Maximum iterations to prevent infinite loops
MAX_ITERATIONS = 15


# ============================================
# Node Implementations
# ============================================

def router_node(state: OrchestratorState) -> dict:
    """
    Route user request to appropriate skill or idle response.

    This node analyzes the user's message and decides:
    1. If a skill should be activated (e.g., task_manager for "create a task")
    2. If this is just casual conversation (idle response)

    Returns:
        Updated state with current_skill set (or None for idle)
    """
    logger.info("Router node: analyzing user intent")

    # Get the last user message first
    last_user_msg = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    if not last_user_msg:
        return {"current_skill": None}

    # ========================================
    # Layer 1: Keyword-based fast detection
    # ========================================
    TASK_KEYWORDS = [
        # Task creation - various patterns
        "创建任务", "新建任务", "添加任务", "建一个任务", "加一个任务",
        "新任务", "一个任务",  # Simpler patterns
        "create task", "add task", "new task",
        # Task modification
        "修改任务", "更新任务", "编辑任务", "改一下任务",
        "update task", "edit task", "modify task",
        # Task deletion
        "删除任务", "移除任务", "删掉任务",
        "delete task", "remove task",
        # Task query
        "查看任务", "列出任务", "任务列表", "有什么任务", "我的任务", "所有任务",
        "list task", "show task", "my task",
        # Task snooze
        "延后任务", "推迟任务", "暂停任务", "snooze",
        # Task completion
        "完成任务", "标记完成", "任务完成",
        "complete task", "mark done", "finish task",
    ]

    NOTE_KEYWORDS = [
        "创建笔记", "新建笔记", "添加笔记", "写笔记",
        "搜索笔记", "查找笔记", "笔记搜索",
        "create note", "add note", "search note", "find note",
    ]

    msg_lower = last_user_msg.lower()
    logger.info(f"Router: User message = '{last_user_msg}'")
    logger.info(f"Router: Checking {len(TASK_KEYWORDS)} task keywords")

    # Check for task keywords
    for keyword in TASK_KEYWORDS:
        if keyword in msg_lower:
            logger.info(f"Router: Keyword match '{keyword}' -> task_manager")
            return {"current_skill": "task_manager"}

    # Check for note keywords
    for keyword in NOTE_KEYWORDS:
        if keyword in msg_lower:
            logger.info(f"Router: Keyword match '{keyword}' -> note_manager")
            return {"current_skill": "note_manager"}

    # ========================================
    # Layer 2: LLM-based intent detection (fallback)
    # ========================================
    logger.info("Router: No keyword match, falling back to LLM")

    # Get available skills
    registry = get_skill_registry()
    skill_descriptions = registry.get_all_skill_descriptions()

    if not skill_descriptions:
        logger.warning("No skills available, routing to idle")
        return {"current_skill": None}

    # Format skill options for LLM
    skill_options = "\n".join([
        f"- {s['name']}: {s['description']}"
        for s in skill_descriptions
    ])

    # Get LLM for routing decision
    model = get_langchain_llm()
    structured_model = model.with_structured_output(SkillActivation)

    # Ask LLM to route
    routing_prompt = f"""Analyze the user's message and decide if a skill should be activated.

Available skills:
{skill_options}

User message: "{last_user_msg}"

Rules:
1. If the user wants to manage tasks (create, update, delete, list, snooze) -> use "task_manager"
2. If the user wants to search or manage notes -> use "note_manager" (if available)
3. If this is just casual chat or greeting -> set should_activate=False
4. Be efficient - don't over-analyze simple requests
"""

    try:
        # Try structured output first
        decision = structured_model.invoke(routing_prompt)

        if decision is None:
            # Fallback: Use regular LLM call with JSON parsing
            logger.warning("Structured output returned None, falling back to JSON parsing")

            # Simplified prompt focused on task detection with Chinese keywords
            simple_prompt = f"""你是一个意图识别路由器。判断用户是否想要管理任务。

用户消息: "{last_user_msg}"

任务管理关键词（包含任意一个即为任务管理）:
- 创建任务/新建任务/添加任务/建一个任务
- 修改任务/更新任务/编辑任务
- 删除任务/移除任务
- 查看任务/列出任务/任务列表/有什么任务
- 延后任务/推迟任务/snooze
- 完成任务/标记完成
- 任何提到"任务"并有动作意图的请求

如果用户想要管理任务，返回:
{{"should_activate": true, "skill_name": "task_manager", "reason": "task management"}}

如果是闲聊或问候，返回:
{{"should_activate": false, "skill_name": null, "reason": "casual chat"}}

只返回JSON，不要其他内容:"""

            response = model.invoke(simple_prompt)
            import json
            import re
            # Extract JSON from response
            content = response.content if hasattr(response, 'content') else str(response)
            logger.info(f"Fallback LLM response: {content[:200]}")

            # Find JSON in content
            json_match = re.search(r'\{[^{}]*\}', content)
            if json_match:
                try:
                    parsed = json.loads(json_match.group())
                    logger.info(f"Parsed JSON: {parsed}")
                    if parsed.get("should_activate") and parsed.get("skill_name"):
                        logger.info(f"Router decision (fallback): skill={parsed['skill_name']}")
                        return {"current_skill": parsed["skill_name"]}
                except json.JSONDecodeError as e:
                    logger.error(f"JSON parse error: {e}")
            else:
                logger.warning("No JSON found in LLM response")
            return {"current_skill": None}

        logger.info(f"Router decision: skill={decision.skill_name}, reason={decision.reason}")

        if decision.should_activate and decision.skill_name:
            return {"current_skill": decision.skill_name}
        else:
            return {"current_skill": None}

    except Exception as e:
        logger.error(f"Router error: {e}")
        return {"current_skill": None}


def loader_node(state: OrchestratorState) -> dict:
    """
    Load skill SOP and prepare tools for specialist.

    This node:
    1. Loads the skill's Markdown SOP
    2. Applies sliding window to message history
    3. Injects SOP as suffix (for KV Cache optimization)
    4. Sets up available tools
    """
    skill_name = state["current_skill"]
    if not skill_name:
        return {}

    logger.info(f"Loader node: loading skill '{skill_name}'")

    try:
        registry = get_skill_registry()
        skill = registry.load_skill(skill_name)

        # Get SOP for injection
        sop_content = registry.get_skill_sop_for_injection(skill_name)

        # Apply sliding window to messages
        windowed_messages = apply_sliding_window(state["messages"], window_size=10)

        return {
            "skill_sop": sop_content,
            "available_tools": skill.tools,
            "messages": windowed_messages,
            "iteration_count": 0,  # Reset iteration counter
        }

    except Exception as e:
        logger.error(f"Loader error: {e}")
        return {
            "skill_sop": None,
            "available_tools": [],
        }


def specialist_node(state: OrchestratorState) -> dict:
    """
    Execute the specialist agent with skill-specific tools.

    This node:
    1. Creates an agent with the skill's tools
    2. Injects SOP into the conversation (suffix injection)
    3. Runs the ReAct loop until task completion
    4. Extracts UI commands from agent output
    """
    logger.info(f"Specialist node: executing with skill '{state['current_skill']}'")

    # Get tools for this skill
    tool_names = state.get("available_tools", [])
    if not tool_names:
        return {
            "messages": [AIMessage(content="No tools available for this skill.")],
            "ui_commands": [],
        }

    try:
        tools = get_tools_by_names(tool_names)
    except Exception as e:
        logger.error(f"Failed to load tools: {e}")
        return {
            "messages": [AIMessage(content=f"Failed to load tools: {e}")],
            "ui_commands": [],
        }

    # Build the agent with SOP injection
    model = get_langchain_llm()
    model_with_tools = model.bind_tools(tools)

    # Prepare messages with SOP suffix injection
    messages = list(state["messages"])

    # Inject SOP as system message at the end (suffix injection)
    sop = state.get("skill_sop")
    if sop:
        messages.append(SystemMessage(content=sop))

    # Build a tool map for quick lookup
    tool_map = {tool.name: tool for tool in tools}

    # Invoke the model
    try:
        response = model_with_tools.invoke(messages)
        logger.info(f"Specialist: Model response tool_calls={response.tool_calls}")

        # Check for tool calls
        if response.tool_calls:
            # Execute tools manually (not using ToolNode to avoid config issues)
            from langchain_core.messages import ToolMessage
            tool_results = []

            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_call_id = tool_call.get("id", f"call_{tool_name}")

                logger.info(f"Specialist: Executing tool {tool_name} with args {tool_args}")

                if tool_name in tool_map:
                    try:
                        # Execute the tool
                        result = tool_map[tool_name].invoke(tool_args)
                        logger.info(f"Specialist: Tool {tool_name} result: {result[:100] if isinstance(result, str) else result}...")
                        tool_results.append(ToolMessage(
                            content=str(result),
                            tool_call_id=tool_call_id,
                            name=tool_name
                        ))
                    except Exception as tool_error:
                        logger.error(f"Specialist: Tool {tool_name} error: {tool_error}")
                        tool_results.append(ToolMessage(
                            content=f"Error executing {tool_name}: {tool_error}",
                            tool_call_id=tool_call_id,
                            name=tool_name
                        ))
                else:
                    tool_results.append(ToolMessage(
                        content=f"Tool {tool_name} not found",
                        tool_call_id=tool_call_id,
                        name=tool_name
                    ))

            # Continue with tool results
            all_messages = messages + [response] + tool_results

            # Get final response after tool execution
            final_response = model_with_tools.invoke(all_messages)
            logger.info(f"Specialist: Final response: {final_response.content[:100] if final_response.content else 'empty'}...")

            # Generate UI commands based on tool calls
            ui_commands = []
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                # Task-related tools trigger task list refresh
                if tool_name.startswith("task_"):
                    ui_commands.append({
                        "type": "refresh",
                        "payload": {"target": "tasks"}
                    })
                    break  # Only need one refresh command
                # Note-related tools trigger note list refresh
                elif tool_name.startswith("note_"):
                    ui_commands.append({
                        "type": "refresh",
                        "payload": {"target": "notes"}
                    })
                    break

            return {
                "messages": [response] + tool_results + [final_response],
                "iteration_count": state.get("iteration_count", 0) + 1,
                "ui_commands": ui_commands,
            }
        else:
            # No tool calls, direct response
            return {
                "messages": [response],
                "iteration_count": state.get("iteration_count", 0) + 1,
            }

    except Exception as e:
        logger.error(f"Specialist error: {e}", exc_info=True)
        return {
            "messages": [AIMessage(content=f"Error during execution: {e}")],
        }


def continue_check(state: OrchestratorState) -> dict:
    """
    Check if there are more tasks to complete.

    This node decides whether to:
    1. Continue with more actions (loop back to specialist)
    2. End the current skill execution

    Uses LLM to analyze if the task is complete.
    """
    iteration_count = state.get("iteration_count", 0)

    # Hard limit on iterations
    if iteration_count >= MAX_ITERATIONS:
        logger.warning(f"Max iterations ({MAX_ITERATIONS}) reached, ending")
        return {"current_skill": None}

    # Get last AI message
    last_ai_msg = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage):
            last_ai_msg = msg
            break

    if not last_ai_msg:
        return {"current_skill": None}

    # If no tool calls in last message, task is likely complete
    if not last_ai_msg.tool_calls:
        logger.info("No pending tool calls, task complete")
        return {"current_skill": None}

    # Otherwise continue
    return {}


def idle_response_node(state: OrchestratorState) -> dict:
    """
    Handle casual conversation when no skill is needed.

    This node provides friendly responses for greetings,
    general questions, and other non-skill requests.
    """
    logger.info("Idle response node: handling casual conversation")

    model = get_langchain_llm()

    # Get the last user message
    last_user_msg = None
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break

    if not last_user_msg:
        return {"messages": [AIMessage(content="Hi! How can I help you today?")]}

    # Simple prompt for casual chat
    system_prompt = """You are a helpful personal assistant for a "Personal Growth OS" application.
You help users manage tasks and notes. Be friendly and concise.

If the user seems to want help with tasks or notes, suggest they can:
- Create, update, or delete tasks
- Search or manage notes
- Schedule and snooze tasks

Keep responses brief and helpful."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=last_user_msg)
    ]

    try:
        response = model.invoke(messages)
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Idle response error: {e}")
        return {"messages": [AIMessage(content="Hi! How can I help you today?")]}


# ============================================
# Routing Functions
# ============================================

def route_after_router(state: OrchestratorState) -> Literal["loader", "idle"]:
    """Decide next node after router."""
    if state.get("current_skill"):
        return "loader"
    return "idle"


def route_after_continue(state: OrchestratorState) -> Literal["specialist", "end"]:
    """Decide whether to continue or end."""
    if state.get("current_skill"):
        return "specialist"
    return "end"


# ============================================
# Graph Construction
# ============================================

def create_orchestrator_graph():
    """
    Create and compile the orchestrator graph.

    Returns:
        Compiled LangGraph runnable with checkpointer
    """
    # Create the graph
    graph = StateGraph(OrchestratorState)

    # Add nodes
    graph.add_node("router", router_node)
    graph.add_node("loader", loader_node)
    graph.add_node("specialist", specialist_node)
    graph.add_node("continue_check", continue_check)
    graph.add_node("idle", idle_response_node)

    # Set entry point
    graph.set_entry_point("router")

    # Add edges
    graph.add_conditional_edges(
        "router",
        route_after_router,
        {
            "loader": "loader",
            "idle": "idle",
        }
    )

    graph.add_edge("loader", "specialist")
    graph.add_edge("specialist", "continue_check")

    graph.add_conditional_edges(
        "continue_check",
        route_after_continue,
        {
            "specialist": "specialist",
            "end": END,
        }
    )

    graph.add_edge("idle", END)

    # Compile with checkpointer
    checkpointer = get_checkpointer()
    return graph.compile(checkpointer=checkpointer)


# ============================================
# Singleton Instance
# ============================================

_orchestrator_instance = None


def get_orchestrator():
    """
    Get the global orchestrator instance.

    Returns:
        Compiled LangGraph orchestrator
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = create_orchestrator_graph()
    return _orchestrator_instance
