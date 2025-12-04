"""
Supervisor Subgraph - 委托和协调研究任务。

负责将大的研究问题分解为多个小的研究任务，并行执行。
"""

from typing import Literal
from datetime import datetime
import asyncio
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from .state import SupervisorState, ConductResearch, ResearchComplete
from .prompts import lead_researcher_prompt
from .researcher_graph import create_researcher_graph
from .tools import think_tool
from app.core.llm_factory import get_langchain_llm


# ==================================================================================
# 辅助函数
# ==================================================================================

def get_today_str() -> str:
    """获取今天的日期字符串"""
    now = datetime.now()
    return f"{now:%a} {now:%b} {now.day}, {now:%Y}"


# ==================================================================================
# Supervisor 节点
# ==================================================================================

async def supervisor_node(
    state: SupervisorState,
    config: RunnableConfig
) -> Command[Literal["supervisor_tools", "__end__"]]:
    """
    Supervisor 节点 - 委托研究任务。

    决定是否需要委托更多研究，还是已经收集到足够信息可以完成。
    """
    llm = get_langchain_llm()

    # 绑定工具（作为结构化输出）
    tools = [ConductResearch, ResearchComplete, think_tool]
    llm_with_tools = llm.bind_tools(tools)

    # 构建 prompt
    system_prompt = lead_researcher_prompt.format(
        date=get_today_str(),
        max_researcher_iterations=6,  # 最多6次迭代
        max_concurrent_research_units=2  # 最多2个并行研究单元
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"研究简报: {state['research_brief']}"),
        *state["supervisor_messages"]
    ]

    # 调用 LLM
    response = await llm_with_tools.ainvoke(messages, config=config)

    # 检查工具调用
    if response.tool_calls:
        # 检查是否调用 ResearchComplete
        for tool_call in response.tool_calls:
            if tool_call["name"] == "ResearchComplete":
                return Command(
                    goto=END,
                    update={"supervisor_messages": [response]}
                )

        # 否则执行工具（ConductResearch 或 think_tool）
        return Command(
            goto="supervisor_tools",
            update={"supervisor_messages": [response]}
        )
    else:
        # 无工具调用，默认结束
        return Command(
            goto=END,
            update={"supervisor_messages": [response]}
        )


# ==================================================================================
# Supervisor Tools 节点
# ==================================================================================

async def supervisor_tools(
    state: SupervisorState,
    config: RunnableConfig
) -> Command[Literal["supervisor"]]:
    """
    执行 Supervisor 工具调用（委托研究）。

    从工具调用中提取 ConductResearch 任务，并行执行，
    然后将结果作为 ToolMessage 返回给 Supervisor。
    """
    last_message = state["supervisor_messages"][-1]
    researcher_graph = create_researcher_graph()

    # 收集 ConductResearch 调用和 think_tool 调用
    research_tasks = []
    think_messages = []

    for tool_call in last_message.tool_calls:
        if tool_call["name"] == "ConductResearch":
            research_tasks.append({
                "tool_call_id": tool_call["id"],
                "research_topic": tool_call["args"]["research_topic"]
            })
        elif tool_call["name"] == "think_tool":
            # 执行 think_tool
            result = think_tool.invoke(tool_call["args"])
            think_messages.append(ToolMessage(
                content=result,
                tool_call_id=tool_call["id"]
            ))

    # 并行执行研究任务
    async def run_research(task):
        """运行单个研究任务"""
        try:
            result = await researcher_graph.ainvoke({
                "researcher_messages": [],
                "research_topic": task["research_topic"],
                "tool_call_iterations": 0,
                "compressed_research": "",
                "raw_notes": []
            }, config=config)

            return {
                "tool_call_id": task["tool_call_id"],
                "result": result["compressed_research"],
                "success": True
            }
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"研究任务失败: {str(e)}", exc_info=True)

            return {
                "tool_call_id": task["tool_call_id"],
                "result": f"研究失败: {str(e)}",
                "success": False
            }

    # 并行执行所有研究任务
    if research_tasks:
        results = await asyncio.gather(*[run_research(task) for task in research_tasks])
    else:
        results = []

    # 构建 ToolMessage
    tool_messages = think_messages.copy()
    new_notes = []

    for res in results:
        tool_messages.append(ToolMessage(
            content=res["result"],
            tool_call_id=res["tool_call_id"]
        ))
        if res["success"]:
            new_notes.append(res["result"])

    # 更新迭代计数
    new_iterations = state["research_iterations"] + 1

    # 检查是否超过最大迭代次数
    MAX_ITERATIONS = 6
    if new_iterations >= MAX_ITERATIONS:
        # 强制结束，添加提示信息
        tool_messages.append(ToolMessage(
            content="已达到最大研究迭代次数，自动结束研究。",
            tool_call_id="system_limit"
        ))

        return Command(
            goto=END,
            update={
                "supervisor_messages": tool_messages,
                "notes": state["notes"] + new_notes,
                "research_iterations": new_iterations
            }
        )
    else:
        return Command(
            goto="supervisor",
            update={
                "supervisor_messages": tool_messages,
                "notes": state["notes"] + new_notes,
                "research_iterations": new_iterations
            }
        )


# ==================================================================================
# 创建 Supervisor 子图
# ==================================================================================

def create_supervisor_graph():
    """
    创建 Supervisor 子图。

    工作流：
    1. supervisor → 决定是否委托研究或完成
    2. supervisor_tools → 执行研究委托（并行）
    3. 返回 supervisor 或 END

    Returns:
        编译后的 StateGraph
    """
    workflow = StateGraph(SupervisorState)

    # 添加节点
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("supervisor_tools", supervisor_tools)

    # 定义流程（Command API 自动处理路由）
    workflow.add_edge(START, "supervisor")

    return workflow.compile()
