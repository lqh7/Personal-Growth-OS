"""
Deep Task Researcher - Multi-layer LangGraph Agent System

参考 open_deep_research 实现，提供任务分解的深度研究能力。

主要组件:
- main_graph.py: 主图（clarify → research_brief → supervisor → final）
- supervisor_graph.py: Supervisor 子图（委托研究任务）
- researcher_graph.py: Researcher 子图（执行具体研究）
- state.py: State 定义和 Pydantic 模型
- prompts.py: 所有 prompt 模板
- tools.py: 工具定义（search_knowledge_base, think_tool）

使用示例:
    from app.agents.deep_researcher import create_deep_task_researcher

    graph = create_deep_task_researcher()
    result = await graph.ainvoke({
        "messages": [HumanMessage(content="准备项目演示PPT")],
        "needs_clarification": False,
        "research_brief": None,
        "supervisor_messages": [],
        "notes": [],
        "final_output": None
    })

    print(result["final_output"])
"""

from .main_graph import create_deep_task_researcher

__all__ = ["create_deep_task_researcher"]
