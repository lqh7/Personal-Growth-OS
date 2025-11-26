# 数据库迁移完成 - PostgreSQL + pgvector

## 迁移状态：✅ 完成

从 SQLite + ChromaDB 双数据库架构成功迁移到 PostgreSQL + pgvector 统一数据库方案。

## 迁移内容

### 已更新的文件
1. **requirements.txt** - 移除 LangChain/ChromaDB，添加 psycopg2-binary/pgvector/sentence-transformers
2. **config.py** - 移除 ChromaDB 配置项
3. **llm_factory.py** - 重写为使用 sentence-transformers
4. **database.py** - PostgreSQL 连接 + pgvector 初始化
5. **models.py** - 新增 NoteEmbedding 向量模型
6. **vector_store.py** - 完全重写，使用 pgvector
7. **notes.py** - 重新启用向量化功能
8. **task_igniter_agno.py** - 集成 pgvector 搜索
9. **.env** - 配置 PostgreSQL 连接

### 数据库信息
- **类型**: PostgreSQL 16+ with pgvector 0.6.0
- **主机**: 139.224.62.197 (通过 SSH 隧道访问)
- **数据库**: personal_growth_os
- **表数量**: 10 个
- **向量维度**: 384 (all-MiniLM-L6-v2)

### 已创建的表
- `tasks` - 任务管理
- `notes` - 笔记存储
- `projects` - 项目组织
- `tags` - 标签系统
- `note_embeddings` ✨ - 向量存储（新增）
- `note_attachments` - 附件管理
- `note_links` - 笔记链接
- `note_tags` - 笔记标签关联
- `search_history` - 搜索历史
- `user_profile_memories` - 用户偏好

## 使用方法

### 1. 启动 SSH 隧道

**必须先建立 SSH 隧道才能连接数据库**

```bash
ssh -L 5432:127.0.0.1:5432 root@139.224.62.197
```

保持这个终端窗口打开。

### 2. 启动后端

新建终端窗口：

```bash
cd backend
start.bat
```

或手动启动：

```bash
cd backend
venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动前端

```bash
cd frontend
npm run dev
```

### 4. 访问应用

- **前端**: http://localhost:5173
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 功能验证

### 测试向量搜索
```bash
# 创建笔记
curl -X POST http://localhost:8000/api/notes/ \
  -H "Content-Type: application/json" \
  -d '{"title":"测试笔记","content":"这是一个关于项目管理的笔记"}'

# 语义搜索
curl "http://localhost:8000/api/notes/search/semantic?query=项目管理&limit=5"
```

### 测试任务点火
```bash
curl -X POST http://localhost:8000/api/tasks/ignite \
  -H "Content-Type: application/json" \
  -d '{"task_description":"准备项目演示PPT"}'
```

## 技术优势

### 相比 SQLite + ChromaDB
- ✅ **单一数据源** - 消除数据同步问题
- ✅ **ACID 事务** - 数据一致性保证
- ✅ **云端部署** - 支持远程访问和备份
- ✅ **原生 SQL** - 可以直接 JOIN 向量和关系数据
- ✅ **更好性能** - pgvector 专为 PostgreSQL 优化

### 依赖简化
- ❌ 移除: `langgraph`, `langchain-*`, `chromadb`, `mem0ai`
- ✅ 添加: `psycopg2-binary`, `pgvector`, `sentence-transformers`

## 注意事项

1. **SSH 隧道**: 必须保持 SSH 隧道连接才能访问数据库
2. **首次启动**: 首次下载 sentence-transformers 模型需要几分钟
3. **向量生成**: 创建/更新笔记时会自动生成向量（后台任务）
4. **密码安全**: 不要将 `.env` 文件提交到 Git

## 故障排查

### 连接失败
```
OperationalError: connection to server at "localhost", port 5432 failed
```
**解决**: 确保 SSH 隧道正在运行

### 数据库不存在
```
FATAL: database "personal_growth_os" does not exist
```
**解决**: 已自动创建，如果仍报错，手动运行：
```bash
python -c "from app.db.database import init_db; init_db()"
```

### pgvector 未安装
**验证**:
```sql
SELECT * FROM pg_available_extensions WHERE name = 'vector';
```

## 迁移日期

2025-11-26

## 相关文档

- `CLAUDE.md` - 已更新，反映新架构
- `doc/数据库迁移指南.md` - 详细迁移步骤
- `doc/系统现状总结.md` - 当前实现状态
