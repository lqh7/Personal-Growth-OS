# 🚀 快速启动指南

## 一键启动（推荐）

### 第一次运行

1. **配置环境变量**
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   ```

   编辑 `.env`，配置你的LLM（选择一个）：

   **选项1: OpenAI（推荐）**
   ```env
   LLM_PROVIDER=openai
   OPENAI_API_KEY=sk-your-key-here
   ```

   **选项2: Claude**
   ```env
   LLM_PROVIDER=claude
   ANTHROPIC_API_KEY=your-key-here
   ```

   **选项3: 本地Ollama（无需API key）**
   ```env
   LLM_PROVIDER=ollama
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3.1:8b
   ```

2. **安装后端依赖**
   ```bash
   cd backend
   python -m venv venv

   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate

   pip install -r requirements.txt
   cd ..
   ```

3. **安装前端依赖**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

### 启动应用

**终端1 - 启动后端：**
```bash
cd backend
venv\Scripts\activate  # Windows
# 或 source venv/bin/activate  # Linux/Mac
python -m uvicorn app.main:app --reload
```

**终端2 - 启动前端：**
```bash
cd frontend
npm run dev
```

**访问应用：**
打开浏览器 → `http://localhost:5173`

## 验证安装

### 1. 检查后端健康状态
```bash
curl http://localhost:8000/health
```

应该返回：
```json
{
  "status": "healthy",
  "llm_provider": "openai",
  "database": "connected"
}
```

### 2. 查看API文档
浏览器访问：`http://localhost:8000/docs`

### 3. 测试任务启动仪式
```bash
curl -X POST "http://localhost:8000/api/tasks/ignite" \
  -H "Content-Type: application/json" \
  -d '{"task_description": "写一份项目总结报告"}'
```

## 功能体验

### 任务管理
1. 点击「任务启动仪式」按钮
2. 输入模糊的任务描述，如"准备明天的会议"
3. AI会自动分解成3-5个子任务
4. 标识最容易开始的"最小可行任务"

### 笔记管理
1. 创建几条笔记（系统会自动向量化）
2. 使用语义搜索功能
3. 输入查询词，如"项目管理"
4. 系统会返回最相关的笔记（基于RAG）

## 常见问题

### Q: ChromaDB初始化失败？
A: 删除 `chroma_data` 文件夹并重启后端

### Q: LLM响应很慢？
A:
- 检查网络连接
- 考虑使用本地Ollama
- 调整timeout设置

### Q: 前端无法连接后端？
A:
- 确保后端在 `http://localhost:8000` 运行
- 检查CORS配置

### Q: 数据库在哪里？
A: SQLite数据库文件在 `backend/personal_growth_os.db`

## 下一步

- 阅读 [README.md](./README.md) 了解完整功能
- 查看 [CLAUDE.md](./CLAUDE.md) 了解架构设计
- 浏览 `doc/` 目录查看详细设计文档

---

**Have fun building your second brain! 🧠**
