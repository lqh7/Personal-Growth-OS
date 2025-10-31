# 后端启动指南

## 最近的重要更新

### ✅ 已完成的修改 (2025-10-31)

1. **Project 模型添加 `color` 字段**
   - 文件: `app/db/models.py`
   - 字段类型: `String(7)`
   - 默认值: `#667eea`
   - 用途: 为前端项目标签提供颜色标识

2. **创建 Projects API 端点**
   - 新文件: `app/api/endpoints/projects.py`
   - 新文件: `app/crud/crud_project.py`
   - 路由已注册到 `/api/projects`

3. **更新 Project Schemas**
   - 文件: `app/schemas/project.py`
   - 所有 schema 都包含 `color` 字段

## ⚠️ 重要: 数据库需要重置

由于我们添加了新字段,旧的数据库schema不兼容,需要重置数据库。

### 方法1: 使用重置脚本 (推荐)

```bash
cd backend
python reset_and_start.py
```

这个脚本会:
1. 自动删除旧数据库
2. 重新创建带有新schema的数据库
3. 启动FastAPI服务器

### 方法2: 手动操作

```bash
cd backend

# 1. 删除旧数据库
rm personal_growth_os.db

# 2. 启动后端 (会自动创建新数据库)
python app/main.py
```

## 📋 首次安装步骤

### 1. 安装Python依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件,填写必要的配置
# 最重要的是 LLM API keys
```

示例 `.env` 内容:
```env
# LLM Provider Configuration
LLM_PROVIDER=openai
LLM_MODEL=gpt-4
OPENAI_API_KEY=sk-your-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1

# Application Settings
DEBUG=true
CORS_ORIGINS=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175"]
```

### 3. 启动后端

```bash
python app/main.py
```

服务器将运行在: http://localhost:8000

## 🔍 验证安装

1. **健康检查**
   ```bash
   curl http://localhost:8000/health
   ```

2. **访问API文档**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

3. **测试Projects API**
   ```bash
   # 创建项目
   curl -X POST http://localhost:8000/api/projects/ \
     -H "Content-Type: application/json" \
     -d '{"name": "测试项目", "color": "#ff5733"}'

   # 获取所有项目
   curl http://localhost:8000/api/projects/
   ```

## 🐛 常见问题

### 问题1: ModuleNotFoundError

**错误**: `ModuleNotFoundError: No module named 'fastapi'`

**解决方案**: 安装依赖
```bash
pip install -r requirements.txt
```

### 问题2: 500 Internal Server Error

**可能原因**: 数据库schema不匹配

**解决方案**: 重置数据库
```bash
rm personal_growth_os.db
python app/main.py
```

### 问题3: 访问 /docs 被禁止

**可能原因**: 可能是浏览器缓存或CORS问题

**解决方案**:
1. 清除浏览器缓存
2. 检查 `.env` 中的 `CORS_ORIGINS` 配置
3. 重启后端服务器

## 📚 API端点总览

### Tasks
- `GET /api/tasks/` - 获取任务列表
- `POST /api/tasks/` - 创建任务
- `GET /api/tasks/{id}` - 获取单个任务
- `PUT /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务
- `POST /api/tasks/ignite` - 任务启动仪式 (AI分解)

### Notes
- `GET /api/notes/` - 获取笔记列表
- `POST /api/notes/` - 创建笔记
- `GET /api/notes/search/semantic` - 语义搜索

### Projects (新增)
- `GET /api/projects/` - 获取项目列表
- `POST /api/projects/` - 创建项目
- `GET /api/projects/{id}` - 获取单个项目
- `PUT /api/projects/{id}` - 更新项目
- `DELETE /api/projects/{id}` - 删除项目

## 🔄 开发流程

### 修改数据库模型后

1. 开发阶段(无重要数据):
   ```bash
   rm personal_growth_os.db
   python app/main.py
   ```

2. 生产环境(有重要数据):
   - 使用 Alembic 创建数据库迁移
   - 这将在后续版本中实现

## 📝 技术栈

- **FastAPI** - Web框架
- **SQLAlchemy** - ORM
- **SQLite** - 数据库
- **LangGraph** - AI Agent编排
- **ChromaDB** - 向量数据库 (RAG)
- **Mem0** - 记忆系统

## 🎯 下一步

- [ ] 实现 Chat API (`/api/chat`)
- [ ] 实现 Review API (`/api/review`)
- [ ] 添加数据库迁移支持 (Alembic)
- [ ] 添加单元测试
- [ ] 添加用户认证
