# Interview Logs - STAR格式技术解决方案文档

本目录存放Personal Growth OS项目的技术解决方案文档，采用面试友好的STAR格式编写。

## 文档索引

| 日期 | 标题 | 分类 | 技术栈 | 难度 |
|------|------|------|--------|------|
| 2025-12-04 | [PostgreSQL pgvector 语义搜索500错误修复](./2025-12-04-pgvector-semantic-search-fix.md) | Backend / Database | pgvector, SQLAlchemy, PostgreSQL | *** |
| 2025-12-03 | [Chat对话流式渲染与Agent架构优化](./2025-12-03-chat-streaming-react-agent.md) | Full-Stack | LangGraph, Vue3, Pinia, SSE | **** |
| 2025-12-02 | [Chat对话功能异步Checkpointer修复](./2025-12-02-chat-checkpointer-async-fix.md) | Backend + Agent | LangGraph, AsyncPostgresSaver, FastAPI | *** |

## 按技术栈分类

### LangGraph / Agent开发
- [2025-12-03 Chat对话流式渲染与Agent架构优化](./2025-12-03-chat-streaming-react-agent.md)
- [2025-12-02 Chat对话功能异步Checkpointer修复](./2025-12-02-chat-checkpointer-async-fix.md)

### 前端 (Vue 3 / Pinia)
- [2025-12-03 Chat对话流式渲染与Agent架构优化](./2025-12-03-chat-streaming-react-agent.md)

### 后端 (FastAPI / PostgreSQL)
- [2025-12-04 PostgreSQL pgvector 语义搜索500错误修复](./2025-12-04-pgvector-semantic-search-fix.md)
- [2025-12-02 Chat对话功能异步Checkpointer修复](./2025-12-02-chat-checkpointer-async-fix.md)

### 数据库 (PostgreSQL / pgvector)
- [2025-12-04 PostgreSQL pgvector 语义搜索500错误修复](./2025-12-04-pgvector-semantic-search-fix.md)

## 按问题类型分类

### Bug修复
- [2025-12-04 PostgreSQL pgvector 语义搜索500错误修复](./2025-12-04-pgvector-semantic-search-fix.md) - SQL语法冲突
- [2025-12-03 Chat对话流式渲染与Agent架构优化](./2025-12-03-chat-streaming-react-agent.md) - 前端渲染问题
- [2025-12-02 Chat对话功能异步Checkpointer修复](./2025-12-02-chat-checkpointer-async-fix.md) - 异步兼容问题

### 架构优化
- [2025-12-03 Chat对话流式渲染与Agent架构优化](./2025-12-03-chat-streaming-react-agent.md) - 迁移到create_react_agent

## 关键技术词索引

### A-C
- `async/await`: [2025-12-02](./2025-12-02-chat-checkpointer-async-fix.md)
- `AsyncConnectionPool`: [2025-12-03](./2025-12-03-chat-streaming-react-agent.md)
- `AsyncPostgresSaver`: [2025-12-02](./2025-12-02-chat-checkpointer-async-fix.md)
- `bindparam`: [2025-12-04](./2025-12-04-pgvector-semantic-search-fix.md)
- `create_react_agent`: [2025-12-03](./2025-12-03-chat-streaming-react-agent.md)
- `cosine distance`: [2025-12-04](./2025-12-04-pgvector-semantic-search-fix.md)

### L-P
- `LangGraph 1.0`: [2025-12-02](./2025-12-02-chat-checkpointer-async-fix.md), [2025-12-03](./2025-12-03-chat-streaming-react-agent.md)
- `lru_cache`: [2025-12-04](./2025-12-04-pgvector-semantic-search-fix.md)
- `pgvector`: [2025-12-04](./2025-12-04-pgvector-semantic-search-fix.md)
- `Pinia`: [2025-12-03](./2025-12-03-chat-streaming-react-agent.md)
- `psycopg3`: [2025-12-02](./2025-12-02-chat-checkpointer-async-fix.md), [2025-12-03](./2025-12-03-chat-streaming-react-agent.md)

### S-Z
- `sentence-transformers`: [2025-12-04](./2025-12-04-pgvector-semantic-search-fix.md)
- `SQLAlchemy`: [2025-12-04](./2025-12-04-pgvector-semantic-search-fix.md)
- `SSE Streaming`: [2025-12-03](./2025-12-03-chat-streaming-react-agent.md)
- `stream_mode`: [2025-12-03](./2025-12-03-chat-streaming-react-agent.md)
- `vector similarity`: [2025-12-04](./2025-12-04-pgvector-semantic-search-fix.md)
- `Vue 3`: [2025-12-03](./2025-12-03-chat-streaming-react-agent.md)

---

## 使用说明

### 面试准备
1. 按难度排序复习文档
2. 关注"面试Q&A"章节
3. 记忆关键技术词和量化指标

### 新增文档
1. 使用STAR格式模板
2. 确保量化指标至少5个
3. 技术关键词10-15个
4. 更新本README索引

---

*最后更新: 2025-12-04*
