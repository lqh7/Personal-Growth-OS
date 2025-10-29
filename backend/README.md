# Personal Growth OS - Backend

FastAPI-based backend for Personal Growth OS MVP.

## 快速开始

### 1. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并配置你的设置：

```bash
cp ../.env.example .env
```

**重要配置项**：
- `LLM_PROVIDER`: 选择 LLM 提供商 (`openai`, `claude`, `ollama`)
- `OPENAI_API_KEY`: 如果使用 OpenAI
- `ANTHROPIC_API_KEY`: 如果使用 Claude
- `OLLAMA_BASE_URL`: 如果使用本地 Ollama

### 3. 运行开发服务器

```bash
# 从 backend 目录运行
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

服务器将在 `http://localhost:8000` 启动

### 4. 访问 API 文档

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API 端点概览

### 任务管理 (`/api/tasks`)

- `GET /api/tasks/` - 列出所有任务
- `POST /api/tasks/` - 创建新任务
- `GET /api/tasks/{id}` - 获取单个任务
- `PUT /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务
- `POST /api/tasks/{id}/snooze` - 延后任务
- `POST /api/tasks/ignite` - **任务启动仪式**（AI 辅助分解）

### 笔记管理 (`/api/notes`)

- `GET /api/notes/` - 列出所有笔记
- `POST /api/notes/` - 创建新笔记（自动向量化）
- `GET /api/notes/{id}` - 获取单个笔记
- `PUT /api/notes/{id}` - 更新笔记
- `DELETE /api/notes/{id}` - 删除笔记
- `GET /api/notes/search/semantic?query=xxx` - **语义搜索**（RAG）
- `GET /api/notes/tags/` - 获取所有标签

## 核心功能示例

### 任务启动仪式 (Task Ignition Ritual)

```bash
curl -X POST "http://localhost:8000/api/tasks/ignite" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "写一份年度总结报告"
  }'
```

返回：
- 分解后的主任务
- 3-5个子任务
- 标识的"最小可行启动任务"
- 相关的历史笔记

### 语义搜索笔记

```bash
curl "http://localhost:8000/api/notes/search/semantic?query=项目管理&limit=5"
```

使用 ChromaDB 进行向量相似度搜索。

## 架构概览

**核心技术栈**：
- **LangGraph** - 主力Agent框架（StateGraph驱动）
- **LangChain Core** - 仅用于基础LLM接口，最小化使用
- **ChromaDB** - 向量数据库用于RAG
- **SQLite** - 关系数据库
- **Mem0** - 长期记忆管理

```
app/
├── api/endpoints/    # API 路由
│   ├── tasks.py      # 任务管理 API + Agent可视化
│   └── notes.py      # 笔记管理 API
├── agents/           # LangGraph Agents（核心）
│   └── task_igniter_agent.py  # StateGraph驱动的任务分解Agent
├── core/             # 核心配置
│   ├── config.py     # 环境配置（支持自定义API URL）
│   └── llm_factory.py  # LLM 工厂（多提供商支持）
├── crud/             # 数据访问层
│   ├── crud_task.py
│   └── crud_note.py
├── db/               # 数据库
│   ├── database.py   # 连接和会话
│   └── models.py     # SQLAlchemy 模型
├── schemas/          # Pydantic 数据验证
│   ├── task.py
│   └── note.py
└── services/         # 业务逻辑服务
    ├── vector_store.py  # ChromaDB RAG 服务
    └── memory_service.py  # Mem0 记忆服务
```

## LangGraph Agent架构

### 任务分解Agent (Task Igniter)

基于**LangGraph StateGraph**构建，完全不依赖LangChain Chain：

```python
# 状态定义
class TaskIgniterState(TypedDict):
    user_input: str
    main_task_title: str
    subtasks: List[Dict]
    status: Literal["init", "analyzing", "decomposing", "completed", "error"]
    ...

# 节点定义
analyze_task_node -> decompose_task_node -> retrieve_notes_node -> finalize

# 条件路由
根据status动态路由，支持错误处理
```

**查看Agent可视化**：
```bash
curl http://localhost:8000/api/tasks/agent/visualization
```

返回Mermaid图，可用于文档和debugging。

## 数据库

使用 SQLite，数据库文件 `personal_growth_os.db` 会在首次启动时自动创建。

### 核心表结构

- `projects` - 项目容器
- `tasks` - 任务（支持 snooze_until 延后功能）
- `notes` - 笔记（content 用于 RAG，source_url 用于可追溯性）
- `tags` - 标签
- `note_tags` - 笔记-标签关联表
- `user_profile_memories` - 用户偏好记忆

## 三层数据存储

1. **SQLite** - 关系数据（事实性数据）
2. **ChromaDB** - 向量存储（知识语料库，用于 RAG）
   - 存储在 `./chroma_data/`
3. **Mem0** - 长期记忆（对话历史和用户偏好）
   - 存储在 `./mem0_data/`

## 开发提示

### 测试 LLM 连接

```python
from app.core.llm_factory import get_chat_model

llm = get_chat_model()
response = llm.invoke("Hello, world!")
print(response.content)
```

### 使用不同的 LLM 提供商

在 `.env` 中更改 `LLM_PROVIDER`：
- `openai` - 需要 OPENAI_API_KEY
- `claude` - 需要 ANTHROPIC_API_KEY
- `ollama` - 需要本地运行 Ollama

## 故障排除

### ChromaDB 初始化错误

如果遇到 ChromaDB 权限问题，删除 `chroma_data` 文件夹并重启。

### Mem0 未安装

Mem0 是可选的。如果未安装，记忆功能将被禁用但不会影响其他功能。

```bash
pip install mem0ai
```

## MVP 限制

当前 MVP 版本不包括：
- 后台定时提醒（需要单独的 Worker 进程）
- 复盘功能的完整实现
- WebSocket 实时通信
- 用户认证系统

这些功能将在后续迭代中添加。
