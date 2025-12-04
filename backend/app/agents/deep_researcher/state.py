"""
Graph state definitions and data structures for the Deep Task Researcher agent.

参考 open_deep_research 的 state 设计，适配任务分解场景。
"""

import operator
from typing import Annotated, Optional, Sequence
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage, MessageLikeRepresentation
from langgraph.graph import MessagesState
from typing_extensions import TypedDict


# ==================================================================================
# Structured Outputs (Pydantic Models for LLM Output)
# ==================================================================================

class ClarifyWithUser(BaseModel):
    """用户澄清结果的结构化输出"""

    need_clarification: bool = Field(
        description="是否需要澄清用户意图"
    )
    question: str = Field(
        description="澄清问题（如果需要澄清）"
    )
    verification: str = Field(
        description="确认消息（如果无需澄清，告知用户即将开始任务分解）"
    )


class ResearchBrief(BaseModel):
    """研究简报的结构化输出"""

    research_brief: str = Field(
        description="详细的任务研究问题描述，用于指导后续的任务分解研究"
    )


class Subtask(BaseModel):
    """子任务的结构化定义"""

    title: str = Field(description="子任务标题（15-30字）")
    description: str = Field(description="子任务描述（50字以内）")
    priority: int = Field(description="优先级 (1-5)", ge=1, le=5)


class TaskDecomposition(BaseModel):
    """任务分解结果的结构化输出"""

    main_task_title: str = Field(description="主任务标题（15-30字）")
    main_task_description: str = Field(description="主任务描述")
    subtasks: list[Subtask] = Field(
        description="3-5个子任务", min_length=3, max_length=5
    )
    minimum_viable_task_index: int = Field(
        description="最小可行任务的索引（0-based，指向最容易开始的子任务）"
    )


class ConductResearch(BaseModel):
    """委托研究任务的工具调用模型"""

    research_topic: str = Field(
        description="研究主题的详细描述（至少一段话，说明要研究什么、为什么研究、期望找到什么）"
    )


class ResearchComplete(BaseModel):
    """研究完成信号（无参数工具）"""
    pass


class Summary(BaseModel):
    """研究摘要的结构化输出（用于压缩研究结果）"""

    summary: str = Field(description="研究摘要")
    key_excerpts: str = Field(description="关键摘录（最多5条）")


# ==================================================================================
# Custom Reducers
# ==================================================================================

def override_reducer(current_value, new_value):
    """
    自定义 reducer：允许覆盖值而非合并。

    用于 supervisor_messages 和 notes 等字段，支持动态更新。
    如果 new_value 是字典且包含 type="override"，则直接替换；
    否则使用 operator.add 合并列表。
    """
    if isinstance(new_value, dict) and new_value.get("type") == "override":
        return new_value.get("value", new_value)
    else:
        # 确保 current_value 是列表
        if current_value is None:
            current_value = []
        return operator.add(current_value, new_value)


# ==================================================================================
# State Definitions
# ==================================================================================

class DeepTaskState(MessagesState):
    """
    主图 State（Deep Task Researcher）

    继承 MessagesState 提供 messages 字段（自动使用 add_messages reducer）。
    额外字段用于跟踪任务分解流程的各个阶段。
    """

    needs_clarification: bool = False
    research_brief: Optional[str] = None
    supervisor_messages: Annotated[
        list[MessageLikeRepresentation], override_reducer
    ] = []
    notes: Annotated[list[str], override_reducer] = []
    final_output: Optional[str] = None


class SupervisorState(TypedDict):
    """
    Supervisor 子图 State

    负责委托和协调多个 Researcher 的研究任务。
    """

    supervisor_messages: Annotated[
        list[MessageLikeRepresentation], override_reducer
    ]
    research_brief: str
    notes: Annotated[list[str], override_reducer]
    research_iterations: int


class ResearcherState(TypedDict):
    """
    Researcher 子图 State

    执行具体的研究任务（搜索知识库、思考、压缩结果）。
    """

    researcher_messages: Annotated[list[MessageLikeRepresentation], operator.add]
    research_topic: str
    tool_call_iterations: int
    compressed_research: str
    raw_notes: Annotated[list[str], override_reducer]


class ResearcherOutputState(BaseModel):
    """
    Researcher 子图的输出 State

    仅包含需要返回给 Supervisor 的字段。
    """

    compressed_research: str
    raw_notes: list[str] = []
