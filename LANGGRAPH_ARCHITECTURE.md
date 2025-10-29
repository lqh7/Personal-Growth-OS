# LangGraph Agent架构设计

## 核心设计原则

本项目采用 **LangGraph** 作为主力Agent框架，遵循以下原则：

1. **StateGraph优先**：所有复杂业务逻辑都使用LangGraph的StateGraph实现
2. **最小化LangChain**：只使用LangChain Core的基础LLM接口，不使用Chain
3. **状态驱动**：通过TypedDict定义清晰的状态模式
4. **节点模块化**：每个节点是独立的处理单元
5. **条件路由**：基于状态动态路由，支持复杂工作流

## 技术栈

```
langgraph==0.2.45          # 主力框架
langgraph-checkpoint-sqlite # 状态持久化
langchain-core==0.3.15     # 仅用于LLM接口
langchain-openai           # OpenAI集成
langchain-anthropic        # Claude集成
```

**完全移除**：
- ❌ `langchain` 完整包
- ❌ LangChain的Chain、Prompt Template、Output Parser

## Agent架构模式

### 1. 任务分解Agent (Task Igniter)

**文件**: `backend/app/agents/task_igniter_agent.py`

#### 状态定义

```python
class TaskIgniterState(TypedDict):
    # 输入
    user_input: str
    project_id: int | None

    # 中间状态
    main_task_title: str
    main_task_description: str
    subtasks: Annotated[List[Dict], add]  # 使用reducer累积
    minimum_viable_task_index: int

    # 检索结果
    related_notes: List[Dict]

    # 控制流
    status: Literal["init", "analyzing", "decomposing", "retrieving", "completed", "error"]
    error_message: str | None
```

#### 节点流程图

```
START
  ↓
analyze_task (分析任务)
  ↓ [error?]
  ├─→ error → END
  ↓ [success]
decompose_task (分解子任务)
  ↓ [error?]
  ├─→ error → END
  ↓ [success]
retrieve_notes (检索相关笔记)
  ↓
finalize (完成)
  ↓
END
```

#### 节点实现

**1. analyze_task_node**
- 输入：用户的模糊任务描述
- 处理：使用LLM提炼主任务标题和描述
- 输出：更新state的`main_task_title`和`main_task_description`

**2. decompose_task_node**
- 输入：主任务信息
- 处理：使用LLM分解为3-5个子任务
- 输出：更新state的`subtasks`和`minimum_viable_task_index`

**3. retrieve_notes_node**
- 输入：主任务描述
- 处理：从ChromaDB检索相关笔记
- 输出：更新state的`related_notes`

**4. finalize_node**
- 处理：标记状态为completed
- 输出：最终状态

#### 条件路由

```python
def route_after_analyze(state: TaskIgniterState) -> Literal["decompose_task", "error"]:
    if state["status"] == "error":
        return "error"
    return "decompose_task"

def route_after_decompose(state: TaskIgniterState) -> Literal["retrieve_notes", "error"]:
    if state["status"] == "error":
        return "error"
    return "retrieve_notes"
```

#### 使用方式

```python
from app.agents.task_igniter_agent import get_task_igniter

agent = get_task_igniter()

# 同步执行
result = agent.invoke(
    user_input="写一份年度总结报告",
    project_id=1
)

# 异步执行
result = await agent.ainvoke(
    user_input="写一份年度总结报告"
)

# 获取可视化
mermaid = agent.get_graph_visualization()
```

## API集成

### 可视化端点

```
GET /api/tasks/agent/visualization
```

返回Agent的Mermaid图，可用于：
- 文档生成
- Debugging
- 监控Agent执行流程

示例：

```bash
curl http://localhost:8000/api/tasks/agent/visualization
```

返回：

```json
{
  "mermaid": "graph TD\n  START --> analyze_task\n  analyze_task --> decompose_task\n  ...",
  "message": "Use this Mermaid diagram to visualize the agent workflow"
}
```

### 任务分解端点

```
POST /api/tasks/ignite
```

内部调用LangGraph Agent：

```python
# 调用Agent
agent_state = agent.invoke(
    user_input=request.task_description,
    project_id=request.project_id
)

# 检查执行状态
if agent_state["status"] == "error":
    raise HTTPException(...)

# 使用Agent返回的状态创建任务
main_task = create_task(
    title=agent_state["main_task_title"],
    description=agent_state["main_task_description"]
)
```

## LLM配置（支持自定义API）

### 环境变量

```.env
# OpenAI（支持自定义代理）
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-xxx
OPENAI_API_BASE=https://your-proxy.com/v1  # 可选

# Claude（支持自定义代理）
LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sk-xxx
ANTHROPIC_API_BASE=https://your-proxy.com  # 可选

# 本地Ollama
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### LLM工厂实现

```python
# backend/app/core/llm_factory.py
def create_chat_model(provider, temperature=0.7):
    if provider == "openai":
        kwargs = {
            "api_key": settings.OPENAI_API_KEY,
            "model": settings.OPENAI_MODEL,
            "temperature": temperature
        }
        # 支持自定义API地址
        if settings.OPENAI_API_BASE:
            kwargs["base_url"] = settings.OPENAI_API_BASE
        return ChatOpenAI(**kwargs)

    elif provider == "claude":
        kwargs = {
            "api_key": settings.ANTHROPIC_API_KEY,
            "model": settings.ANTHROPIC_MODEL,
            "temperature": temperature
        }
        if settings.ANTHROPIC_API_BASE:
            kwargs["base_url"] = settings.ANTHROPIC_API_BASE
        return ChatAnthropic(**kwargs)
```

## 状态持久化（可选）

LangGraph支持Checkpoint机制，用于：
- 长期运行的工作流
- 支持中断和恢复
- 审计和调试

### 启用Checkpointing

```python
from langgraph.checkpoint.memory import MemorySaver

checkpointer = MemorySaver()
graph = builder.compile(checkpointer=checkpointer)

# 使用thread_id跟踪会话
config = {"configurable": {"thread_id": "user_123_session_1"}}
result = graph.invoke(initial_state, config)
```

### SQLite Checkpointer（生产环境）

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
graph = builder.compile(checkpointer=checkpointer)
```

## 未来扩展

### 1. 多Agent协作

参考开源项目模式：
- **Supervisor模式**：一个supervisor agent协调多个worker agents
- **Sequential模式**：多个agents按顺序执行
- **Parallel模式**：多个agents并行执行并聚合结果

### 2. Human-in-the-Loop

```python
from langgraph.prebuilt import ToolNode

# 添加人工确认节点
def human_approval_node(state):
    # 等待人工确认
    approval = wait_for_approval(state)
    return {"approved": approval}

builder.add_node("human_approval", human_approval_node)
builder.add_conditional_edges(
    "decompose_task",
    lambda s: "human_approval" if s["needs_review"] else "retrieve_notes"
)
```

### 3. 工具集成

```python
from langgraph.prebuilt import ToolNode, tools_condition

# 定义工具
tools = [search_tool, calculator_tool, database_query_tool]

# 创建工具节点
tool_node = ToolNode(tools)

builder.add_node("tools", tool_node)
builder.add_conditional_edges("agent", tools_condition)
```

## 最佳实践

1. **状态最小化**：只在state中保留必要信息
2. **节点单一职责**：每个节点只做一件事
3. **错误处理**：每个节点都应处理异常并更新status
4. **类型安全**：使用TypedDict和Literal明确类型
5. **可视化优先**：使用Mermaid图文档化Agent流程
6. **测试驱动**：为每个节点编写单元测试

## 参考资料

- [LangGraph官方文档](https://langchain-ai.github.io/langgraph/)
- [开源项目参考](doc/agent参考.text)
  - open_deep_research - 研究型Agent
  - joyagent-jdgenie - 多Agent协作

---

**记住**：LangGraph是主力，LangChain只是工具！
