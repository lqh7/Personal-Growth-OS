"""
Task Igniter Agent using LangGraph StateGraph.
任务启动仪式 - 基于LangGraph的有状态Agent，完全不依赖LangChain Chain。

Architecture Pattern:
1. State-driven: 使用TypedDict定义状态
2. Node-based: 每个节点是独立的处理单元
3. Conditional routing: 基于状态动态路由
4. Checkpointing: 支持状态持久化
"""

from typing import TypedDict, Literal, Annotated, List, Dict, Any
from typing_extensions import TypedDict
from operator import add
import json

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.core.llm_factory import get_chat_model


# ============================================================================
# 1. 定义状态 State Schema
# ============================================================================

class TaskIgniterState(TypedDict):
    """
    Agent的状态定义 - LangGraph的核心
    每个节点都接收这个状态，并返回部分更新
    """
    # 输入
    user_input: str
    project_id: int | None

    # 中间状态
    main_task_title: str
    main_task_description: str
    subtasks: Annotated[List[Dict[str, Any]], add]  # 使用add reducer累积子任务
    minimum_viable_task_index: int

    # 检索结果
    related_notes: List[Dict[str, Any]]

    # 控制流
    status: Literal["init", "analyzing", "decomposing", "retrieving", "completed", "error"]
    error_message: str | None


# ============================================================================
# 2. 定义节点 Nodes - 每个节点是一个独立的处理单元
# ============================================================================

def analyze_task_node(state: TaskIgniterState) -> Dict[str, Any]:
    """
    节点1: 分析用户输入，提炼出主任务的标题和描述
    """
    llm = get_chat_model(temperature=0.7)

    prompt = f"""作为任务规划助手，分析用户的任务描述并提炼出清晰的主任务。

用户输入：{state['user_input']}

请返回JSON格式（不要包含markdown代码块标记）：
{{
    "title": "精炼的任务标题（15字以内）",
    "description": "清晰的任务描述（50字以内）"
}}"""

    try:
        response = llm.invoke(prompt)
        # 清理可能的markdown代码块标记
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        result = json.loads(content)

        return {
            "main_task_title": result["title"],
            "main_task_description": result["description"],
            "status": "analyzing"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"分析任务失败: {str(e)}"
        }


def decompose_task_node(state: TaskIgniterState) -> Dict[str, Any]:
    """
    节点2: 将主任务分解为3-5个可执行的子任务
    """
    llm = get_chat_model(temperature=0.7)

    prompt = f"""作为任务分解专家，将以下任务分解为3-5个具体可执行的子任务。

主任务：{state['main_task_title']}
描述：{state['main_task_description']}

分解原则：
1. 每个子任务要具体、可执行
2. 第一个子任务应该是最容易开始的（最小可行任务）
3. 按逻辑顺序排列
4. 每个子任务15-30字

请返回JSON格式（不要包含markdown代码块标记）：
{{
    "subtasks": [
        {{"title": "子任务1标题", "description": "详细描述", "priority": 1}},
        {{"title": "子任务2标题", "description": "详细描述", "priority": 2}}
    ],
    "minimum_viable_index": 0
}}

minimum_viable_index是数组索引（从0开始），指向最容易开始的任务。"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1]
            content = content.rsplit("```", 1)[0]

        result = json.loads(content)

        return {
            "subtasks": result["subtasks"],
            "minimum_viable_task_index": result.get("minimum_viable_index", 0),
            "status": "decomposing"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": f"分解任务失败: {str(e)}"
        }


def retrieve_related_notes_node(state: TaskIgniterState) -> Dict[str, Any]:
    """
    节点3: 从向量数据库检索相关笔记
    这里只是模拟，实际会调用vector_store服务
    """
    # TODO: 实际集成ChromaDB检索
    # from app.services.vector_store import get_vector_store
    # vector_store = get_vector_store()
    # results = vector_store.search_similar_notes(state['main_task_description'], n_results=5)

    # 暂时返回空列表
    return {
        "related_notes": [],
        "status": "retrieving"
    }


def finalize_node(state: TaskIgniterState) -> Dict[str, Any]:
    """
    节点4: 最终化处理，标记为完成
    """
    return {
        "status": "completed"
    }


# ============================================================================
# 3. 定义路由逻辑 Routing Logic
# ============================================================================

def route_after_analyze(state: TaskIgniterState) -> Literal["decompose_task", "error"]:
    """
    条件路由：分析后的下一步
    """
    if state["status"] == "error":
        return "error"
    return "decompose_task"


def route_after_decompose(state: TaskIgniterState) -> Literal["retrieve_notes", "error"]:
    """
    条件路由：分解后的下一步
    """
    if state["status"] == "error":
        return "error"
    return "retrieve_notes"


def error_handler_node(state: TaskIgniterState) -> Dict[str, Any]:
    """
    错误处理节点
    """
    return {"status": "error"}


# ============================================================================
# 4. 构建StateGraph
# ============================================================================

def build_task_igniter_graph():
    """
    构建任务启动仪式的StateGraph

    流程图：
    START -> analyze_task -> decompose_task -> retrieve_notes -> finalize -> END
               |                   |
               v (error)           v (error)
             error               error
    """
    # 创建StateGraph
    builder = StateGraph(TaskIgniterState)

    # 添加节点
    builder.add_node("analyze_task", analyze_task_node)
    builder.add_node("decompose_task", decompose_task_node)
    builder.add_node("retrieve_notes", retrieve_related_notes_node)
    builder.add_node("finalize", finalize_node)
    builder.add_node("error", error_handler_node)

    # 定义边
    builder.add_edge(START, "analyze_task")

    # 条件边：根据状态路由
    builder.add_conditional_edges(
        "analyze_task",
        route_after_analyze,
        {
            "decompose_task": "decompose_task",
            "error": "error"
        }
    )

    builder.add_conditional_edges(
        "decompose_task",
        route_after_decompose,
        {
            "retrieve_notes": "retrieve_notes",
            "error": "error"
        }
    )

    builder.add_edge("retrieve_notes", "finalize")
    builder.add_edge("finalize", END)
    builder.add_edge("error", END)

    # 编译 - 可以添加checkpointer实现状态持久化
    # checkpointer = MemorySaver()
    # graph = builder.compile(checkpointer=checkpointer)
    graph = builder.compile()

    return graph


# ============================================================================
# 5. Agent执行接口
# ============================================================================

class TaskIgniterAgent:
    """
    任务启动仪式Agent - LangGraph驱动
    """

    def __init__(self):
        self.graph = build_task_igniter_graph()

    def invoke(self, user_input: str, project_id: int | None = None) -> TaskIgniterState:
        """
        执行任务分解

        Args:
            user_input: 用户的任务描述
            project_id: 项目ID（可选）

        Returns:
            完整的状态对象，包含所有分解结果
        """
        initial_state: TaskIgniterState = {
            "user_input": user_input,
            "project_id": project_id,
            "main_task_title": "",
            "main_task_description": "",
            "subtasks": [],
            "minimum_viable_task_index": 0,
            "related_notes": [],
            "status": "init",
            "error_message": None
        }

        # 调用graph执行
        final_state = self.graph.invoke(initial_state)

        return final_state

    async def ainvoke(self, user_input: str, project_id: int | None = None) -> TaskIgniterState:
        """异步执行"""
        initial_state: TaskIgniterState = {
            "user_input": user_input,
            "project_id": project_id,
            "main_task_title": "",
            "main_task_description": "",
            "subtasks": [],
            "minimum_viable_task_index": 0,
            "related_notes": [],
            "status": "init",
            "error_message": None
        }

        final_state = await self.graph.ainvoke(initial_state)
        return final_state

    def get_graph_visualization(self) -> str:
        """
        获取图的Mermaid可视化
        用于debugging和文档
        """
        return self.graph.get_graph().draw_mermaid()


# 便捷函数
def get_task_igniter() -> TaskIgniterAgent:
    """获取TaskIgniter Agent实例"""
    return TaskIgniterAgent()
