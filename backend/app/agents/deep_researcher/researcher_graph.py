"""
Researcher Subgraph - 执行具体的研究任务。

负责搜索知识库、思考、并压缩研究结果。
"""

from typing import Literal
from datetime import datetime
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from .state import ResearcherState, ResearcherOutputState, Summary
from .prompts import research_system_prompt, compress_research_system_prompt, compress_research_simple_human_message
from .tools import search_knowledge_base, think_tool
from app.core.llm_factory import get_langchain_llm


# ==================================================================================
# 辅助函数
# ==================================================================================

def get_today_str() -> str:
    """获取今天的日期字符串"""
    now = datetime.now()
    return f"{now:%a} {now:%b} {now.day}, {now:%Y}"


# ==================================================================================
# Researcher 节点
# ==================================================================================

async def researcher_node(
    state: ResearcherState,
    config: RunnableConfig
) -> Command[Literal["researcher_tools", "compress_research"]]:
    """
    Researcher 节点 - 使用工具搜索和思考。

    这个节点调用 LLM 并绑定工具（search_knowledge_base, think_tool）。
    LLM 会决定是否调用工具，如果调用则路由到 researcher_tools，
    否则直接进入压缩阶段。
    """
    llm = get_langchain_llm()

    # 绑定工具
    tools = [search_knowledge_base, think_tool]
    llm_with_tools = llm.bind_tools(tools)

    # 构建 prompt
    system_prompt = research_system_prompt.format(
        date=get_today_str(),
        mcp_prompt=""  # 暂不使用 MCP
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"研究主题: {state['research_topic']}"),
        *state["researcher_messages"]
    ]

    # 调用 LLM
    response = await llm_with_tools.ainvoke(messages, config=config)

    # 检查是否有工具调用
    if response.tool_calls:
        return Command(
            goto="researcher_tools",
            update={"researcher_messages": [response]}
        )
    else:
        # 无工具调用，进入压缩阶段
        return Command(
            goto="compress_research",
            update={"researcher_messages": [response]}
        )


# ==================================================================================
# Researcher Tools 节点
# ==================================================================================

async def researcher_tools(
    state: ResearcherState,
    config: RunnableConfig
) -> Command[Literal["researcher", "compress_research"]]:
    """
    执行工具调用。

    从最后一条消息中提取工具调用，执行工具，返回 ToolMessage。
    根据迭代次数决定是继续研究还是进入压缩阶段。
    """
    last_message = state["researcher_messages"][-1]
    tool_messages = []

    # 执行所有工具调用
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        # 调用对应工具
        if tool_name == "search_knowledge_base":
            result = search_knowledge_base.invoke(tool_args)
        elif tool_name == "think_tool":
            result = think_tool.invoke(tool_args)
        else:
            result = f"未知工具: {tool_name}"

        tool_messages.append(ToolMessage(
            content=result,
            tool_call_id=tool_call["id"]
        ))

    # 更新迭代计数
    new_iterations = state["tool_call_iterations"] + 1

    # 检查是否超过最大迭代次数
    MAX_ITERATIONS = 10  # 最多10次工具调用
    if new_iterations >= MAX_ITERATIONS:
        # 超过限制，强制进入压缩阶段
        return Command(
            goto="compress_research",
            update={
                "researcher_messages": tool_messages,
                "tool_call_iterations": new_iterations
            }
        )
    else:
        # 继续研究
        return Command(
            goto="researcher",
            update={
                "researcher_messages": tool_messages,
                "tool_call_iterations": new_iterations
            }
        )


# ==================================================================================
# Compress Research 节点
# ==================================================================================

async def compress_research(
    state: ResearcherState,
    config: RunnableConfig
) -> ResearcherOutputState:
    """
    压缩研究结果。

    将研究过程中的所有消息和工具调用结果压缩为简洁的摘要。
    使用 structured output 确保返回格式化的 Summary 对象。
    """
    llm = get_langchain_llm()

    # 使用 structured output
    structured_llm = (
        llm
        .with_structured_output(Summary)
        .with_retry(stop_after_attempt=3)
    )

    # 构建压缩 prompt
    system_prompt = compress_research_system_prompt.format(date=get_today_str())

    messages = [
        SystemMessage(content=system_prompt),
        *state["researcher_messages"],
        HumanMessage(content=compress_research_simple_human_message)
    ]

    try:
        summary = await structured_llm.ainvoke(messages, config=config)

        # 格式化摘要
        formatted_summary = f"### 研究摘要\n\n{summary.summary}\n\n### 关键摘录\n\n{summary.key_excerpts}"

        return ResearcherOutputState(
            compressed_research=formatted_summary,
            raw_notes=state.get("raw_notes", []) + [formatted_summary]
        )

    except Exception as e:
        # 如果压缩失败，返回原始消息内容
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"研究结果压缩失败: {str(e)}", exc_info=True)

        # 提取所有消息内容作为后备
        fallback_content = "\n\n".join([
            msg.content for msg in state["researcher_messages"]
            if hasattr(msg, "content") and msg.content
        ])

        return ResearcherOutputState(
            compressed_research=f"研究结果（原始）:\n\n{fallback_content}",
            raw_notes=state.get("raw_notes", [])
        )


# ==================================================================================
# 创建 Researcher 子图
# ==================================================================================

def create_researcher_graph():
    """
    创建 Researcher 子图。

    工作流：
    1. researcher → 调用 LLM 决定是否使用工具
    2. researcher_tools → 执行工具调用
    3. compress_research → 压缩研究结果并返回

    Returns:
        编译后的 StateGraph
    """
    workflow = StateGraph(
        ResearcherState,
        output=ResearcherOutputState
    )

    # 添加节点
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("researcher_tools", researcher_tools)
    workflow.add_node("compress_research", compress_research)

    # 定义流程（Command API 自动处理路由）
    workflow.add_edge(START, "researcher")

    return workflow.compile()
