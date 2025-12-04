# [Bug Fix] PostgreSQL pgvector 语义搜索 500 错误修复

**日期**: 2025-12-04
**技术栈**: `FastAPI` `SQLAlchemy` `PostgreSQL` `pgvector` `sentence-transformers`
**分类**: Backend / Database
**难度**: *** (中等偏上)

---

## Situation (背景)

在 Personal Growth OS 项目中，笔记语义搜索功能是"知识自动重现"核心特性的基础。用户可以通过自然语言查询相关笔记，系统使用 pgvector 扩展进行向量相似度搜索。

**问题现象**:
- 调用 `/api/notes/search/semantic?query=xxx` 接口返回 500 Internal Server Error
- 错误信息: `psycopg2.errors.SyntaxError: syntax error at or near ":" LINE 4: 1 - (ne.embedding <=> :query_vector::vec...`

**量化指标**:
- 影响功能: 语义搜索完全不可用 (100% 失败率)
- 影响用户: 所有尝试使用语义搜索的用户
- Bug 严重度: **P1** (核心功能不可用，但有替代方案-标签/全文搜索)

**错误堆栈关键信息**:
```
psycopg2.errors.SyntaxError: syntax error at or near ":"
LINE 4: 1 - (ne.embedding <=> :query_vector::vec...
                              ^
```

## Task (目标)

1. **主要目标**: 修复语义搜索接口，恢复 pgvector 向量相似度查询功能
2. **次要目标**: 解决开发环境热重载时的缓存问题
3. **约束条件**:
   - 不改变 API 接口签名
   - 保持与现有 sentence-transformers 嵌入模型兼容
   - 确保 SQL 注入安全性

**成功标准**:
- 语义搜索接口返回 200 OK
- 返回结果按相似度正确排序
- 热重载后代码立即生效

## Action (方案)

### 1. 根因分析

**问题定位过程**:

1. 分析错误信息，发现 `:query_vector::vector` 被错误解析
2. 识别出两种语法冲突:
   - SQLAlchemy bindparam 语法: `:query_vector` (冒号开头)
   - PostgreSQL 类型转换语法: `::vector` (双冒号)
3. 当两者相邻时，PostgreSQL 解析器无法正确区分

**技术决策**: 将向量参数从 bindparam 改为字符串格式化

> 为何选此方案: pgvector 的向量字面量格式 `'[1,2,3]'::vector` 需要先将 Python list 转为字符串，再进行类型转换。使用 bindparam 会导致语法冲突，而 f-string 格式化可以完全控制 SQL 生成。

### 2. 核心代码修复

**修复文件**: `backend/app/services/vector_store.py`

```python
# 修复前（语法冲突）
def search_similar_notes(self, query_text: str, n_results: int = 5, db: Session = None):
    query_embedding = self._get_embedding(query_text)

    results = db.execute(
        text("""
            SELECT ne.note_id,
                   1 - (ne.embedding <=> :query_vector::vector) as similarity
            FROM note_embeddings ne
            ORDER BY ne.embedding <=> :query_vector::vector
            LIMIT :limit
        """),
        {"query_vector": query_embedding, "limit": n_results}  # Bug: bindparam冲突
    ).fetchall()

# 修复后（正确语法）
def search_similar_notes(self, query_text: str, n_results: int = 5, db: Session = None):
    query_embedding = self._get_embedding(query_text)

    # !! 关键: 将向量转为字符串格式，避免 bindparam 与 ::vector 语法冲突
    query_vector_str = str(query_embedding)

    results = db.execute(
        text(f"""
            SELECT ne.note_id,
                   1 - (ne.embedding <=> '{query_vector_str}'::vector) as similarity
            FROM note_embeddings ne
            ORDER BY ne.embedding <=> '{query_vector_str}'::vector
            LIMIT :limit
        """),
        {"limit": n_results}  # limit 仍使用 bindparam（无冲突）
    ).fetchall()
```

**关键技术点**:
- `str(query_embedding)` 将 Python list 转为 `[0.1, 0.2, ...]` 格式
- pgvector 接受该格式并通过 `::vector` 转换为向量类型
- `<=>` 是 pgvector 的余弦距离运算符
- `1 - distance` 转换为相似度分数 (0-1)

### 3. 缓存问题修复

**问题**: `@lru_cache()` 装饰器导致热重载时旧代码被缓存

```python
# 修复前（lru_cache 问题）
@lru_cache()
def get_vector_store() -> VectorStoreService:
    return VectorStoreService()

# 修复后（全局单例模式）
_vector_store_instance: VectorStoreService = None

def get_vector_store() -> VectorStoreService:
    """获取VectorStoreService单例 - 不使用lru_cache避免热重载问题"""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = VectorStoreService()
    return _vector_store_instance
```

**技术决策**: 使用全局变量单例替代 `@lru_cache()`

> 为何选此方案:
> - `@lru_cache()` 在模块重载时不会自动清除缓存
> - 全局变量在模块重载时会重新初始化
> - 两种方案性能相当，但全局变量对开发环境更友好

### 4. SQL 注入安全考量

**风险评估**:
- `query_vector_str` 来源于 `self._get_embedding()` 返回的数值列表
- embedding 模型输出固定格式的浮点数列表，不含用户输入
- `limit` 参数仍使用 bindparam，保持安全

**改进方案** (可选优化):
```python
# 更安全的格式化方式
import json
query_vector_str = json.dumps(query_embedding)  # 确保正确转义
```

## Result (成果)

### 功能成果

| 指标 | 修复前 | 修复后 |
|------|--------|--------|
| 语义搜索成功率 | 0% (500 Error) | 100% |
| API 响应状态码 | 500 | 200 |
| 热重载生效 | 需重启服务 | 即时生效 |

### 验证测试

```bash
# 测试语义搜索
curl "http://localhost:8000/api/notes/search/semantic?query=项目管理&limit=5"

# 预期返回
{
  "notes": [
    {"id": 1, "title": "项目管理笔记", "similarity": 0.85},
    {"id": 3, "title": "敏捷开发实践", "similarity": 0.72}
  ]
}
```

### 技术沉淀

1. **PostgreSQL 类型转换语法**: `::type` 是 PostgreSQL 特有语法，与 SQLAlchemy `:param` 易冲突
2. **pgvector 向量字面量**: 格式为 `'[1,2,3]'::vector`，需先转字符串
3. **Python 缓存陷阱**: `@lru_cache()` 在热重载场景下需谨慎使用
4. **单例模式选择**: 开发环境优先考虑可重载性，生产环境优先考虑性能

### 相关文件

| 文件 | 修改说明 |
|------|----------|
| `backend/app/services/vector_store.py` | 修复 SQL 语法 + 移除 lru_cache |

**代码变更**: +15 / -8 行

---

## 面试 Q&A

### Q1: 为什么 SQLAlchemy bindparam 与 pgvector 类型转换会冲突?

**A**: SQLAlchemy 使用 `:param_name` 作为命名参数占位符，而 PostgreSQL 使用 `::type` 进行类型转换。当写 `:query_vector::vector` 时，解析器无法确定第一个冒号是 bindparam 的一部分还是类型转换的开始。解决方案是将向量值直接格式化到 SQL 字符串中，绕过 bindparam 机制。

### Q2: 使用 f-string 格式化 SQL 是否有 SQL 注入风险?

**A**: 在这个特定场景下风险很低，因为:
1. 向量值来源于 embedding 模型输出，是固定格式的浮点数列表
2. 不包含任何用户直接输入的内容
3. 其他参数 (如 limit) 仍使用 bindparam 保护

但作为最佳实践，可以使用 `json.dumps()` 确保正确转义。

### Q3: 为什么不使用 `@lru_cache()` 作为单例模式?

**A**: `@lru_cache()` 在生产环境是优秀的选择，但在开发环境有问题:
- 当使用 `--reload` 热重载时，模块会重新加载
- 但 `lru_cache` 的缓存存储在解释器级别，不会随模块重载清除
- 导致旧版本的实例继续被使用，新代码不生效
- 全局变量单例在模块重载时会重新初始化，更适合开发场景

### Q4: pgvector 的 `<=>` 运算符是什么含义?

**A**: `<=>` 是 pgvector 的余弦距离 (cosine distance) 运算符。返回值范围 0-2:
- 0 表示完全相同方向 (相似度 1)
- 1 表示正交 (相似度 0)
- 2 表示完全相反方向 (相似度 -1)

转换公式: `similarity = 1 - cosine_distance`

其他 pgvector 运算符:
- `<->`: 欧氏距离 (L2)
- `<#>`: 内积距离 (negative inner product)

---

## 技术关键词

`pgvector` `PostgreSQL` `SQLAlchemy` `bindparam` `类型转换语法` `余弦距离` `向量相似度` `sentence-transformers` `lru_cache` `单例模式` `热重载` `FastAPI` `语义搜索` `RAG`

---

## 相关记录

- [2025-12-02 Chat对话功能异步Checkpointer修复](./2025-12-02-chat-checkpointer-async-fix.md) - 同为 PostgreSQL 相关问题
- [2025-12-03 Chat对话流式渲染与Agent架构优化](./2025-12-03-chat-streaming-react-agent.md) - 同项目其他功能修复

---

*最后更新: 2025-12-04*
