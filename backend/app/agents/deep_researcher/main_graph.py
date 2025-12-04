"""
Main Graph - Deep Task Researcher 主图。

完整的任务分解研究流程：
1. clarify → 澄清用户意图
2. write_research_brief → 生成研究简报
3. research_supervisor → 委托研究（调用 Supervisor 子图）
4. final_decomposition → 生成最终任务分解
"""

from typing import Literal
from datetime import datetime
from langgraph.graph import StateGraph, END, START
from langgraph.types import Command
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig

from .state import DeepTaskState, ClarifyWithUser, ResearchBrief, TaskDecomposition
from .prompts import (
    clarify_with_user_instructions,
    transform_messages_into_research_topic_prompt,
    final_report_generation_prompt
)
from .supervisor_graph import create_supervisor_graph
from app.core.llm_factory import get_langchain_llm
from app.core.langgraph_checkpoint import get_checkpointer


# ==================================================================================
# 辅助函数
# ==================================================================================

def get_today_str() -> str:
    """获取今天的日期字符串"""
    now = datetime.now()
    return f"{now:%a} {now:%b} {now.day}, {now:%Y}"


def format_messages(messages) -> str:
    """格式化消息历史为文本"""
    formatted = []
    for msg in messages:
        if hasattr(msg, "type"):
            role = "User" if msg.type == "human" else "Assistant"
        else:
            role = "Unknown"

        content = msg.content if hasattr(msg, "content") else str(msg)
        formatted.append(f"{role}: {content}")

    return "\n".join(formatted)


def format_task_decomposition(decomposition: TaskDecomposition) -> str:
    """格式化任务分解结果为 Markdown"""
    output = f"# 📝 {decomposition.main_task_title}\n\n"
    output += f"**描述**: {decomposition.main_task_description}\n\n"
    output += "## 🔹 子任务列表\n\n"

    for i, subtask in enumerate(decomposition.subtasks):
        # 标记最小可行任务
        if i == decomposition.minimum_viable_task_index:
            marker = "⭐"
        else:
            marker = f"{i+1}."

        output += f"{marker} **{subtask.title}** (优先级: {subtask.priority})\n"
        output += f"   {subtask.description}\n\n"

    return output


# ==================================================================================
# 主图节点
# ==================================================================================

async def clarify_node(
    state: DeepTaskState,
    config: RunnableConfig
) -> Command[Literal["write_research_brief", "__end__"]]:
    """
    澄清节点 - 检查是否需要澄清用户意图。

    如果需要澄清，返回问题给用户并结束；
    否则继续到下一阶段。
    """
    llm = get_langchain_llm()

    # 使用 structured output + retry
    structured_llm = (
        llm
        .with_structured_output(ClarifyWithUser)
        .with_retry(stop_after_attempt=3)
    )

    # 构建 prompt
    prompt = clarify_with_user_instructions.format(
        messages=format_messages(state["messages"]),
        date=get_today_str()
    )

    result = await structured_llm.ainvoke([HumanMessage(content=prompt)], config=config)

    if result.need_clarification:
        # 需要澄清，返回问题给用户
        return Command(
            goto=END,
            update={
                "needs_clarification": True,
                "messages": [AIMessage(content=result.question)]
            }
        )
    else:
        # 无需澄清，继续下一步
        return Command(
            goto="write_research_brief",
            update={
                "needs_clarification": False,
                "messages": [AIMessage(content=result.verification)]
            }
        )


async def write_research_brief(
    state: DeepTaskState,
    config: RunnableConfig
) -> Command[Literal["research_supervisor"]]:
    """
    生成研究简报。

    将用户消息转化为详细的任务分解研究问题。
    """
    llm = get_langchain_llm()

    structured_llm = (
        llm
        .with_structured_output(ResearchBrief)
        .with_retry(stop_after_attempt=3)
    )

    prompt = transform_messages_into_research_topic_prompt.format(
        messages=format_messages(state["messages"]),
        date=get_today_str()
    )

    result = await structured_llm.ainvoke([HumanMessage(content=prompt)], config=config)

    return Command(
        goto="research_supervisor",
        update={"research_brief": result.research_brief}
    )


async def research_supervisor(
    state: DeepTaskState,
    config: RunnableConfig
) -> Command[Literal["final_decomposition"]]:
    """
    委托给 Supervisor 子图执行研究。

    Supervisor 会将研究问题分解为多个子任务，并行执行。
    """
    supervisor_graph = create_supervisor_graph()

    result = await supervisor_graph.ainvoke({
        "supervisor_messages": [],
        "research_brief": state["research_brief"],
        "notes": [],
        "research_iterations": 0
    }, config=config)

    return Command(
        goto="final_decomposition",
        update={
            "supervisor_messages": result["supervisor_messages"],
            "notes": result["notes"]
        }
    )


async def final_decomposition(
    state: DeepTaskState,
    config: RunnableConfig
) -> Command[Literal["__end__"]]:
    """
    最终任务分解。

    基于研究结果，生成结构化的任务分解方案。
    """
    llm = get_langchain_llm()

    structured_llm = (
        llm
        .with_structured_output(TaskDecomposition)
        .with_retry(stop_after_attempt=3)
    )

    # 构建 prompt
    # 将 final_report_generation_prompt 适配为任务分解场景
    base_prompt = final_report_generation_prompt.format(
        research_brief=state["research_brief"],
        messages=format_messages(state["messages"]),
        date=get_today_str(),
        findings="\n\n".join(state["notes"]) if state["notes"] else "暂无研究结果，请基于常识进行任务分解。"
    )

    # 添加任务分解特定指令
    task_prompt = base_prompt + """

**任务分解要求**：

你需要基于研究结果，生成一个结构化的任务分解方案。返回 JSON 格式，包含以下字段：

{
  "main_task_title": "主任务标题（15-30字）",
  "main_task_description": "主任务描述（详细说明任务的目标和背景）",
  "subtasks": [
    {
      "title": "子任务1标题",
      "description": "子任务1描述（50字以内，说明具体要做什么）",
      "priority": 3  // 优先级 1-5，数字越小越重要
    },
    // ... 3-5个子任务
  ],
  "minimum_viable_task_index": 0  // 最小可行任务的索引（0-based，指向最容易开始的子任务）
}

**子任务分解原则**：
1. 每个子任务要具体、可执行、有明确的完成标准
2. 第一个子任务应该是最容易开始的（降低启动摩擦）
3. 按逻辑顺序排列子任务（考虑依赖关系）
4. 每个子任务标题15-30字，描述50字以内
5. 优先级：1=最高优先级，5=最低优先级

**使用用户语言**：
- 如果用户消息是中文，所有输出必须是中文
- 如果用户消息是英文，所有输出必须是英文
"""

    try:
        result = await structured_llm.ainvoke([HumanMessage(content=task_prompt)], config=config)

        # 格式化输出
        formatted_output = format_task_decomposition(result)

        return Command(
            goto=END,
            update={
                "final_output": formatted_output,
                "messages": [AIMessage(content=formatted_output)]
            }
        )

    except Exception as e:
        # 如果结构化输出失败，使用回退方案
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"任务分解失败: {str(e)}", exc_info=True)

        error_message = f"任务分解过程遇到错误: {str(e)}\n\n请手动分解任务，或重新尝试。"

        return Command(
            goto=END,
            update={
                "final_output": error_message,
                "messages": [AIMessage(content=error_message)]
            }
        )


# ==================================================================================
# 创建主图
# ==================================================================================

def create_deep_task_researcher():
    """
    创建 Deep Task Researcher 主图。

    完整流程：
    1. clarify → 澄清用户意图（可能提前结束）
    2. write_research_brief → 生成研究简报
    3. research_supervisor → 委托研究（调用 Supervisor 子图）
    4. final_decomposition → 生成最终任务分解

    Returns:
        编译后的 StateGraph（带 checkpointer）
    """
    workflow = StateGraph(DeepTaskState)

    # 添加节点
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("write_research_brief", write_research_brief)
    workflow.add_node("research_supervisor", research_supervisor)
    workflow.add_node("final_decomposition", final_decomposition)

    # 定义流程（Command API 自动处理路由）
    workflow.add_edge(START, "clarify")

    # 编译（带 checkpointer 用于持久化）
    checkpointer = get_checkpointer()
    if checkpointer:
        return workflow.compile(checkpointer=checkpointer)
    else:
        # 后备方案：无 checkpointer 编译
        import logging
        logger = logging.getLogger(__name__)
        logger.warning("Checkpointer 未初始化，Deep Task Researcher 将不支持会话持久化")
        return workflow.compile()
