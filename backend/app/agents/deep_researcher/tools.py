"""
Tools for the Deep Task Researcher agent.

实现知识库搜索和战略思考工具。
"""

from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional


# ==================================================================================
# Tool 1: 知识库搜索（RAG）
# ==================================================================================

class SearchKnowledgeArgs(BaseModel):
    """搜索知识库的参数"""

    query: str = Field(description="搜索关键词或问题")
    limit: int = Field(default=5, description="返回结果数量（最多10条）", ge=1, le=10)


@tool(args_schema=SearchKnowledgeArgs)
def search_knowledge_base(query: str, limit: int = 5) -> str:
    """
    在知识库中搜索相关笔记。

    使用语义搜索找到与查询最相关的笔记内容，帮助任务分解时提供上下文信息。

    Args:
        query: 搜索关键词或问题
        limit: 返回结果数量（默认5条）

    Returns:
        格式化的搜索结果字符串，包含笔记标题、内容摘要、相似度分数
    """
    from app.services.vector_store import get_vector_store
    from app.crud import crud_note
    from app.db.database import get_db

    try:
        # 获取数据库会话
        db = next(get_db())

        # 调用 vector store 搜索
        vector_store = get_vector_store()
        results = vector_store.search_similar_notes(db, query, n_results=limit)

        if not results:
            return "未找到相关笔记。建议基于常识和最佳实践进行任务分解。"

        # 格式化输出
        output = f"找到 {len(results)} 条相关笔记:\n\n"

        for i, result in enumerate(results):
            note = crud_note.get_note(db, result["note_id"])
            if note:
                score = result["score"]
                output += f"--- 笔记 {i+1} (相似度: {score:.2f}) ---\n"
                output += f"标题: {note.title}\n"

                # 内容摘要（最多200字符）
                content_preview = note.content[:200] if note.content else ""
                if len(note.content) > 200:
                    content_preview += "..."
                output += f"内容摘要: {content_preview}\n"

                # 来源URL（如果有）
                if note.source_url:
                    output += f"来源: {note.source_url}\n"

                output += "\n"

        return output

    except Exception as e:
        # 错误处理
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"知识库搜索失败: {str(e)}", exc_info=True)
        return f"知识库搜索出错: {str(e)}。请基于常识继续任务分解。"


# ==================================================================================
# Tool 2: 战略思考工具
# ==================================================================================

@tool
def think_tool(reflection: str) -> str:
    """
    战略思考工具 - 用于反思研究进展和规划下一步。

    在每次搜索或工具调用后使用此工具，系统性地评估当前进展并决定下一步行动。
    这创建了研究工作流中的刻意暂停，以进行高质量的决策。

    何时使用：
    - 收到搜索结果后：我找到了哪些关键信息？
    - 决定下一步之前：我是否有足够的信息来全面回答？
    - 评估研究差距时：我还缺少哪些具体信息？
    - 结束研究之前：我现在可以提供完整的答案吗？

    反思应该解决：
    1. 当前研究结果分析 - 我收集了哪些具体信息？
    2. 差距评估 - 还缺少哪些关键信息？
    3. 质量评估 - 我是否有足够的证据/示例来提供好的答案？
    4. 战略决策 - 我应该继续搜索还是提供我的答案？

    Args:
        reflection: 对研究进展、发现、差距和下一步的详细反思

    Returns:
        确认反思已记录用于决策的消息
    """
    return f"思考已记录: {reflection}"


# ==================================================================================
# 辅助函数
# ==================================================================================

def get_all_tools():
    """
    获取所有可用工具的列表。

    Returns:
        工具对象列表
    """
    return [search_knowledge_base, think_tool]
