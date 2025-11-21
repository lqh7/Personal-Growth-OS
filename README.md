# Personal Growth OS

> 你的第二大脑，个人成长的操作系统

一个专为个人成长而设计的智能助手系统，通过AI辅助帮助你对抗拖延、固化知识、驱动复盘。

## 核心特性

### 🚀 支柱一：行动点火器 (The Initiator)
- **任务启动仪式**: AI自动将模糊的大任务分解为3-5个可执行的子任务
- **最小可行启动任务**: 智能识别最容易开始的第一步，降低行动门槛
- **灵活延后**: 支持任务Snooze功能，在合适的时间重新提醒

### 🧠 支柱二：记忆外包大脑 (The Retainer)
- **无缝知识捕获**: 快速创建笔记，支持Markdown格式
- **智能标签系统**: 自动关联和组织知识
- **语义搜索(RAG)**: 基于ChromaDB的向量检索，自动找到相关笔记
- **可追溯性**: 每条笔记可保存来源URL，确保知识可信

### 📊 支柱三：自我优化引擎 (The Optimizer)
- **按需复盘**: 手动触发任务完成情况分析
- **数据洞察**: 识别任务模式和拖延倾向（后续版本完善）

## 技术架构

### 前端
- **Vue 3** + **TypeScript** + **Vite**
- **Element Plus** UI组件库
- **Pinia** 状态管理
- **Vue Router** 路由管理

### 后端
- **FastAPI** - 高性能Python Web框架
- **Agno** - 轻量级AI多智能体框架
- **SQLAlchemy** + **SQLite** - 关系数据库
- **ChromaDB** - 向量数据库（RAG知识检索）

### AI集成
- **可配置LLM提供商**: 支持OpenAI、Claude、Ollama（本地）
- **多智能体系统**: 基于Agno的Agent和Team协作
- **任务分解Agent**: 智能任务规划与分解
- **内置记忆系统**: 自动学习用户偏好和习惯

## 快速开始

### 前置要求

- **Python 3.10+**
- **Node.js 18+**
- **npm/yarn**

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/Personal-Growth-OS.git
cd Personal-Growth-OS
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置你的LLM提供商：

```env
# 选择LLM提供商: openai, claude, 或 ollama
LLM_PROVIDER=openai

# 如果使用OpenAI
OPENAI_API_KEY=your_api_key_here

# 如果使用Claude
ANTHROPIC_API_KEY=your_api_key_here

# 如果使用本地Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### 3. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 启动服务
python -m uvicorn app.main:app --reload
```

后端将在 `http://localhost:8000` 启动

### 4. 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

前端将在 `http://localhost:5173` 启动

### 5. 访问应用

打开浏览器访问: `http://localhost:5173`

## API 文档

后端启动后，访问以下地址查看API文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 核心功能演示

### 任务启动仪式

```bash
# 使用API测试
curl -X POST "http://localhost:8000/api/tasks/ignite" \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "准备下周的项目演示"
  }'
```

返回结果：
- 主任务 + 分解的3-5个子任务
- 标识的"最小可行启动任务"
- 从知识库检索的相关笔记

### 语义搜索笔记

```bash
curl "http://localhost:8000/api/notes/search/semantic?query=项目管理&limit=5"
```

基于向量相似度返回最相关的笔记。

## 项目结构

```
Personal-Growth-OS/
├── backend/              # FastAPI后端
│   ├── app/
│   │   ├── api/          # API路由
│   │   ├── agents/       # AI Agents
│   │   ├── core/         # 核心配置
│   │   ├── crud/         # 数据访问层
│   │   ├── db/           # 数据库模型
│   │   ├── schemas/      # Pydantic模型
│   │   └── services/     # 业务逻辑
│   └── requirements.txt
│
├── frontend/             # Vue 3前端
│   ├── src/
│   │   ├── api/          # API客户端
│   │   ├── components/   # Vue组件
│   │   ├── layouts/      # 布局组件
│   │   ├── stores/       # Pinia状态管理
│   │   ├── views/        # 页面视图
│   │   └── types/        # TypeScript类型
│   └── package.json
│
├── doc/                  # 设计文档
│   ├── 需求.md
│   ├── 详细设计.md
│   └── 工程架构.md
│
├── .env.example          # 环境变量模板
├── CLAUDE.md             # Claude Code开发指南
└── README.md             # 本文件
```

## 开发指南

详见 [CLAUDE.md](./CLAUDE.md) 了解项目架构和开发规范。

## MVP限制

当前版本是最小可用原型(MVP)，以下功能将在后续版本实现：

- ✅ 任务CRUD和AI辅助分解
- ✅ 笔记管理和RAG语义搜索
- ✅ 基础UI界面
- ⏳ 后台定时提醒Worker
- ⏳ 完整的复盘仪表盘和数据可视化
- ⏳ 深度对话式复盘
- ⏳ 浏览器插件（快速捕获知识）
- ⏳ 用户认证和多用户支持

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

---

**Built with ❤️ for personal growth**