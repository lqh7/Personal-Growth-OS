# RAG系统详细设计文档 (llama-index方案)

> **📌 当前实现状态**
> - **RAG框架**: ✅ **llama-index 0.14.6** - 专业RAG数据框架
> - **向量存储**: ✅ **PostgreSQL + pgvector** - 通过llama-index PGVectorStore管理
> - **已实现功能**:
>   - ✅ 自动文档索引 (llama-index VectorStoreIndex)
>   - ✅ 自动embedding生成和存储
>   - ✅ 笔记语义搜索API (`/notes/search/semantic`)
>   - ✅ pgvector索引优化 (IVFFlat自动管理)
> - **核心优势**:
>   - ✅ 自动化程度高 - 无需手动管理embedding和chunking
>   - ✅ 专业RAG能力 - 内置多种查询引擎和chunking策略
>   - ✅ pgvector原生集成 - PGVectorStore开箱即用
>
> 本文档描述基于 **llama-index 0.14.6** 的RAG系统架构,纯文字说明不含代码示例。

---

**版本**: v2.0 (llama-index版本)
**更新日期**: 2025-12-01
**文档类型**: 技术架构设计
**目标受众**: 开发团队

---

## 文档摘要

本文档描述Personal Growth OS项目的笔记知识库RAG系统架构。系统采用**llama-index 0.14.6**专业RAG框架,实现笔记知识的自动化索引、智能检索和精准召回。

**核心特性**:
- **自动文档管理**: llama-index Document抽象统一文档处理
- **智能分块策略**: SentenceWindow、Semantic、Token等多种策略
- **向量自动化**: embedding自动生成、存储和索引优化
- **灵活查询引擎**: VectorStoreQueryEngine、RetrieverQueryEngine、SubQuestionQueryEngine
- **pgvector集成**: PGVectorStore原生支持,无需手写SQL
- **增量更新**: insert/delete API支持动态维护索引

---

## 目录

1. [系统愿景与核心能力](#1-系统愿景与核心能力)
2. [llama-index架构概览](#2-llama-index架构概览)
3. [核心组件说明](#3-核心组件说明)
4. [数据流程设计](#4-数据流程设计)
5. [检索策略设计](#5-检索策略设计)
6. [性能优化方案](#6-性能优化方案)
7. [未来演进方向](#7-未来演进方向)

---

## 1. 系统愿景与核心能力

### 1.1 解决的核心问题

**问题1：知识碎片化**
- 大量笔记难以定位特定知识点
- 解决方案: llama-index自动索引,支持语义检索定位相关内容

**问题2：检索效率低**
- 关键词搜索噪音大,无法理解语义相似性
- 解决方案: 基于向量相似度的语义检索,理解用户真实意图

**问题3：上下文丢失**
- 检索片段脱离原文语境
- 解决方案: llama-index Node Parser保留文档结构,支持上下文扩展

### 1.2 llama-index核心优势

**专业RAG框架**:
- 专门为LLM应用设计的数据框架
- 内置RAG最佳实践和优化策略
- 持续更新适应最新研究成果

**自动化程度高**:
- 自动文档分块 (多种策略可选)
- 自动embedding生成和存储
- 自动索引创建和优化
- 自动元数据提取和管理

**pgvector原生集成**:
- PGVectorStore组件开箱即用
- 自动创建向量表和索引
- 无需手写pgvector SQL查询
- 自动优化索引性能 (IVFFlat/HNSW)

**灵活查询能力**:
- 多种QueryEngine类型
- 混合检索支持 (向量+文本)
- Postprocessor重排序和过滤
- 多步推理能力

---

## 2. llama-index架构概览

### 2.1 系统整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    应用层 (Application)                  │
│   - FastAPI endpoints (/notes/search/semantic)          │
│   - LangGraph Agent (调用RAG检索)                       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              llama-index服务层 (Service)                 │
│   - QueryEngine: 查询引擎                                │
│   - Retriever: 检索器                                    │
│   - Postprocessor: 后处理器                             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│            llama-index核心层 (Core)                      │
│   - ServiceContext: LLM + Embed + NodeParser配置        │
│   - VectorStoreIndex: 向量索引管理                      │
│   - Document/Node: 文档抽象                             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│          向量存储层 (Vector Storage)                     │
│   - PGVectorStore: PostgreSQL + pgvector集成            │
│   - 自动索引优化 (IVFFlat/HNSW)                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 数据流向

**索引流程** (Note创建/更新时):
1. Note模型 → llama-index Document对象
2. Document → Node Parser分块 → Node列表
3. Node → Embedding Model → 向量化
4. 向量 + 元数据 → PGVectorStore存储
5. 自动创建/更新pgvector索引

**查询流程** (语义搜索时):
1. 用户查询 → QueryEngine
2. 查询文本 → Embedding Model → 查询向量
3. 查询向量 → PGVectorStore相似度搜索
4. 检索结果 → Postprocessor过滤/重排序
5. 最终结果 → 返回给上层

---

## 3. 核心组件说明

### 3.1 Document (文档抽象)

**作用**: 统一的文档数据结构

**关键字段**:
- text: 文档文本内容
- metadata: 元数据字典
  - note_id: 笔记ID
  - title: 笔记标题
  - tags: 标签列表
  - created_at: 创建时间
  - updated_at: 更新时间
  - source_url: 来源URL

**生命周期**:
- 创建: 从Note模型转换为Document
- 处理: 经过Node Parser分块
- 存储: 转换为Node存储到向量库

### 3.2 Node Parser (文档分块器)

**作用**: 将长文档智能分割为语义完整的块

**支持的分块策略**:

1. **SentenceWindowNodeParser** (推荐用于笔记)
   - 以句子为基本单位分块
   - 保留前后句子作为上下文窗口
   - 适合需要上下文的场景
   - 参数: window_size (窗口大小), window_metadata_key

2. **SemanticSplitterNodeParser**
   - 基于语义相似度分块
   - 动态确定分块边界
   - 适合语义连贯性强的长文本
   - 参数: buffer_size, breakpoint_percentile_threshold

3. **TokenTextSplitter**
   - 基于token数量分块
   - 简单高效,适合结构化文本
   - 参数: chunk_size, chunk_overlap

4. **MarkdownNodeParser**
   - Markdown结构感知分块
   - 按标题层级分割
   - 保留文档结构信息
   - 参数: None (自动识别Markdown结构)

**选择策略**:
- 短笔记 (<1000字): 不分块,整体索引
- 中等笔记 (1000-5000字): SentenceWindowNodeParser
- 长笔记 (>5000字): SemanticSplitterNodeParser或MarkdownNodeParser
- 结构化笔记 (Markdown): MarkdownNodeParser

### 3.3 ServiceContext (服务上下文)

**作用**: 统一管理llama-index组件配置

**核心组件**:
- **LLM**: 用于查询理解和答案生成
  - OpenAI: GPT-4, GPT-3.5-turbo
  - Anthropic: Claude-3.5-sonnet
  - 本地: Ollama模型

- **Embed Model**: 用于文本向量化
  - OpenAI: text-embedding-3-small (1536维)
  - 本地: sentence-transformers模型 (384维)
  - 配置: 通过`core/llm_factory.py::get_llamaindex_embed_model()`

- **Node Parser**: 文档分块策略
  - 可配置多种策略
  - 支持动态切换

- **Prompt Helper**: Token管理
  - 自动处理context window限制
  - chunk size自适应调整

**配置方式**:
- 全局配置: 创建ServiceContext实例传递给所有组件
- 按需配置: 为不同场景创建不同ServiceContext

### 3.4 PGVectorStore (向量存储)

**作用**: PostgreSQL + pgvector集成组件

**核心功能**:
- 自动创建向量表 (table_name可配置)
- 自动生成pgvector索引
- 支持混合查询 (向量相似度 + 元数据过滤)
- 增量更新 (insert/delete/update)

**表结构** (自动创建):
- id: 主键
- text: 原始文本
- metadata_: JSON元数据
- embedding: vector类型 (维度根据模型自动确定)

**索引优化**:
- IVFFlat索引: 适合中等规模数据 (万级)
- HNSW索引: 适合大规模数据 (百万级)
- 自动选择索引类型和参数

**连接配置**:
- 通过DATABASE_URL环境变量配置
- 自动处理连接池和事务

### 3.5 VectorStoreIndex (向量索引)

**作用**: 向量索引管理的核心组件

**核心方法**:
- from_documents(): 从Document列表创建索引
- insert(): 插入新文档
- delete(): 删除文档
- update(): 更新文档
- as_query_engine(): 创建查询引擎

**索引流程**:
1. 接收Document列表
2. 通过Node Parser分块
3. 通过Embed Model生成向量
4. 存储到PGVectorStore
5. 返回索引实例

**持久化**:
- 索引状态持久化到PostgreSQL
- 无需本地缓存文件
- 支持分布式访问

### 3.6 QueryEngine (查询引擎)

**作用**: 提供统一的查询接口

**查询引擎类型**:

1. **VectorStoreQueryEngine** (基础向量检索)
   - 基于余弦相似度检索top-k结果
   - 参数: similarity_top_k (返回数量)
   - 适合: 简单语义搜索场景

2. **RetrieverQueryEngine** (高级检索)
   - 支持自定义Retriever
   - 支持Postprocessor链
   - 参数: retriever, node_postprocessors
   - 适合: 需要过滤、重排序的复杂场景

3. **SubQuestionQueryEngine** (多步推理)
   - 自动分解复杂问题为子问题
   - 分别检索后综合答案
   - 参数: query_engine_tools (多个子引擎)
   - 适合: 复杂多步问题

**查询流程**:
1. 接收查询文本
2. 生成查询向量
3. 调用Retriever检索
4. Postprocessor后处理
5. LLM生成最终答案 (可选)
6. 返回结果

### 3.7 Retriever (检索器)

**作用**: 从索引中检索相关节点

**检索器类型**:

1. **VectorIndexRetriever**
   - 纯向量相似度检索
   - 参数: similarity_top_k

2. **KeywordTableRetriever**
   - 关键词检索
   - 适合精确匹配场景

3. **HybridRetriever** (推荐)
   - 结合向量检索和关键词检索
   - 参数: vector_retriever, keyword_retriever, mode

**检索模式**:
- AND: 必须同时满足向量和关键词条件
- OR: 满足任一条件即可
- RECIPROCAL_RANK: 融合两种检索分数

### 3.8 Postprocessor (后处理器)

**作用**: 对检索结果进行过滤、重排序、扩展

**后处理器类型**:

1. **SimilarityPostprocessor**
   - 过滤低相似度结果
   - 参数: similarity_cutoff (阈值)

2. **KeywordNodePostprocessor**
   - 关键词过滤
   - 参数: required_keywords, excluded_keywords

3. **MetadataReplacementPostprocessor**
   - 元数据增强
   - 替换Node内容为更丰富的上下文

4. **SentenceEmbeddingOptimizer**
   - 重排序优化
   - 基于query-doc相关性重新排序

5. **PrevNextNodePostprocessor**
   - 上下文扩展
   - 自动获取前后Node补充上下文

**处理链**:
- 支持多个Postprocessor串联
- 顺序执行,逐步精炼结果

---

## 4. 数据流程设计

### 4.1 笔记索引流程

**触发时机**:
- 创建新笔记 (POST /api/notes/)
- 更新笔记内容 (PUT /api/notes/{id})
- 批量重建索引 (管理员操作)

**完整流程**:

1. **获取笔记数据**
   - 从Note模型获取: id, title, content, tags, created_at等

2. **构建Document对象**
   - 组装text: f"{title}\n\n{content}"
   - 组装metadata: {note_id, title, tags, created_at, updated_at}

3. **智能分块 (Node Parser)**
   - 判断笔记长度选择分块策略
   - 短笔记: 不分块
   - 中长笔记: SentenceWindowNodeParser
   - Markdown笔记: MarkdownNodeParser

4. **生成embedding**
   - 通过Embed Model向量化每个Node
   - 自动缓存避免重复计算

5. **存储到pgvector**
   - PGVectorStore.add()方法
   - 自动插入向量表
   - 自动更新索引

6. **返回索引ID**
   - 记录索引状态到Note模型

**优化策略**:
- 批量索引: 一次处理多个Note减少数据库往返
- 增量更新: 只索引新增/修改的Note
- 异步处理: 后台任务队列处理耗时索引

### 4.2 语义搜索流程

**API端点**: GET /api/notes/search/semantic?query=xxx&limit=5

**完整流程**:

1. **接收查询请求**
   - 查询文本: "如何优化RAG性能"
   - 返回数量: limit=5

2. **创建QueryEngine**
   - 从VectorStoreIndex.as_query_engine()创建
   - 配置similarity_top_k=limit
   - 配置Postprocessor (可选)

3. **查询向量化**
   - 通过Embed Model生成查询向量
   - 维度与索引向量一致

4. **pgvector相似度搜索**
   - PGVectorStore.query()方法
   - SQL: SELECT ... ORDER BY embedding <=> query_vector LIMIT 5
   - 使用pgvector索引加速

5. **元数据过滤** (可选)
   - 按tags过滤
   - 按时间范围过滤
   - 按note_id过滤

6. **后处理**
   - SimilarityPostprocessor: 过滤低分结果
   - PrevNextNodePostprocessor: 扩展上下文

7. **组装返回结果**
   - 包含: note_id, title, matched_text, score
   - 按score降序排列

8. **缓存机制** (可选)
   - 缓存热门查询结果
   - TTL: 5分钟

### 4.3 增量更新流程

**笔记更新时**:
1. 删除旧索引: PGVectorStore.delete(note_id)
2. 重新索引: 按索引流程处理更新后的Note

**笔记删除时**:
1. 软删除Note: 标记deleted=True
2. 删除索引: PGVectorStore.delete(note_id)

**批量重建索引**:
1. 获取所有active Notes
2. 清空向量表 (TRUNCATE)
3. 批量索引所有Notes
4. 重建pgvector索引

---

## 5. 检索策略设计

### 5.1 纯向量检索 (基础场景)

**适用场景**: 简单语义搜索

**实现方式**:
- VectorStoreQueryEngine
- similarity_top_k=5
- 无Postprocessor

**查询流程**:
1. 查询向量化
2. pgvector余弦相似度搜索
3. 返回top-5结果

**优点**: 简单快速,适合大部分场景
**缺点**: 可能返回不相关但相似的结果

### 5.2 混合检索 (推荐场景)

**适用场景**: 需要兼顾语义和精确匹配

**实现方式**:
- HybridRetriever
- vector_retriever + keyword_retriever
- mode='RECIPROCAL_RANK'

**查询流程**:
1. 并行执行向量检索和关键词检索
2. 融合两种检索分数
3. 重新排序
4. 返回融合结果

**优点**: 检索准确度高,召回率高
**缺点**: 计算开销较大

### 5.3 过滤增强检索 (精准场景)

**适用场景**: 需要按元数据条件筛选

**实现方式**:
- RetrieverQueryEngine
- 添加MetadataFilter
- 添加SimilarityPostprocessor

**查询流程**:
1. 向量检索
2. 元数据过滤 (tags, date_range等)
3. 相似度阈值过滤
4. 返回过滤后结果

**优点**: 结果精准,噪音少
**缺点**: 可能漏掉相关但不符合条件的结果

### 5.4 上下文扩展检索 (完整场景)

**适用场景**: 需要完整上下文理解

**实现方式**:
- RetrieverQueryEngine
- 添加PrevNextNodePostprocessor

**查询流程**:
1. 向量检索匹配的Node
2. 自动获取前后相邻Node
3. 组合为完整段落
4. 返回扩展结果

**优点**: 上下文完整,理解准确
**缺点**: 返回内容较长

### 5.5 多步推理检索 (复杂场景)

**适用场景**: 复杂多步问题

**实现方式**:
- SubQuestionQueryEngine
- 多个子QueryEngine

**查询流程**:
1. LLM分解复杂问题为子问题
2. 每个子问题独立检索
3. 综合子问题答案
4. 生成最终答案

**优点**: 处理复杂问题能力强
**缺点**: 计算开销大,延迟高

---

## 6. 性能优化方案

### 6.1 索引优化

**pgvector索引类型选择**:
- 数据量 < 1万: 不使用索引(顺序扫描足够快)
- 数据量 1万-100万: IVFFlat索引
- 数据量 > 100万: HNSW索引

**IVFFlat参数**:
- lists: 数据量的平方根 (如10万数据 → 316 lists)
- probes: lists的10% (如316 lists → 32 probes)

**HNSW参数**:
- m: 16 (默认值,适合大部分场景)
- ef_construction: 64
- ef_search: 40

**索引创建**: llama-index PGVectorStore自动管理

### 6.2 查询优化

**缓存策略**:
- ServiceContext缓存: 全局单例
- QueryEngine缓存: 为热门查询创建专用引擎
- Embedding缓存: 缓存查询向量减少重复计算

**批量查询**:
- 支持批量query一次性检索
- 减少数据库往返次数

**懒加载**:
- 索引按需加载
- Node内容延迟获取

### 6.3 embedding优化

**模型选择**:
- 快速场景: sentence-transformers本地模型 (推理快)
- 高质量场景: OpenAI text-embedding-3-small

**向量维度**:
- 降维: 384维 (本地模型) vs 1536维 (OpenAI)
- 权衡: 检索质量 vs 存储/计算开销

**批量embedding**:
- 一次处理多个文本
- GPU加速 (如果可用)

### 6.4 数据库优化

**连接池**:
- 配置合理的连接池大小
- 避免连接耗尽

**查询优化**:
- 使用EXPLAIN分析查询计划
- 确保pgvector索引被使用

**分区** (未来):
- 按时间分区向量表
- 提升大规模数据查询性能

### 6.5 性能监控

**关键指标**:
- 索引速度: 每秒处理文档数
- 查询延迟: P50/P95/P99
- 检索准确率: Recall@k
- 索引大小: 磁盘占用

**监控工具**:
- LangSmith: llama-index集成可观测性
- PostgreSQL慢查询日志
- 自定义性能日志

---

## 7. 未来演进方向

### 7.1 近期优化 (1-3个月)

**增强分块策略**:
- 实现Markdown结构感知分块
- 自适应chunk size选择
- 保留代码块完整性

**元数据丰富**:
- 提取关键词作为metadata
- 识别笔记主题分类
- 记录笔记关系图谱

**检索质量优化**:
- 实现Reranker模型重排序
- 添加相关性反馈机制
- 优化相似度阈值

### 7.2 中期规划 (3-6个月)

**多模态支持**:
- 图片文本提取和索引
- PDF/Word文档解析
- 代码片段专门处理

**高级查询**:
- 时间范围过滤
- 标签组合查询
- 笔记关系图谱查询

**性能提升**:
- 实现查询结果缓存
- 优化大规模数据索引
- 引入HNSW索引

### 7.3 长期愿景 (6-12个月)

**智能推荐**:
- 基于用户行为的笔记推荐
- 相关笔记自动关联
- 知识图谱可视化

**协作功能**:
- 共享知识库RAG
- 团队笔记语义搜索
- 权限控制

**持续学习**:
- 用户反馈优化检索
- A/B测试不同策略
- 自动调优参数

---

## 8. 技术细节补充

### 8.1 llama-index vs 手动实现对比

| 特性 | llama-index | 手动实现 (sentence-transformers) |
|------|-------------|--------------------------------|
| 文档分块 | 内置多种策略 | 需自己实现 |
| Embedding管理 | 自动生成和存储 | 手动调用模型和SQL |
| 索引优化 | 自动创建pgvector索引 | 手动SQL配置 |
| 查询引擎 | 多种类型开箱即用 | 只有基础余弦相似度 |
| 元数据管理 | 自动提取和过滤 | 手动管理JSON字段 |
| 增量更新 | insert/delete API | 手动SQL CRUD |
| 代码维护 | 框架更新自动受益 | 需持续维护所有代码 |
| 开发效率 | 高 (几十行代码) | 低 (数百行代码) |

### 8.2 关键配置示例说明

**ServiceContext配置**:
- 配置LLM用于查询理解
- 配置Embed Model用于向量化
- 配置Node Parser用于分块
- 配置Prompt Helper管理token

**PGVectorStore配置**:
- 数据库连接URL
- 表名 (默认: data_{collection})
- 向量维度 (自动从模型获取)
- Hybrid search支持

**QueryEngine配置**:
- similarity_top_k: 返回结果数量
- response_mode: 响应模式 (compact/tree_summarize/simple_summarize)
- node_postprocessors: 后处理器链
- streaming: 是否流式输出

### 8.3 常见问题处理

**Q: 如何处理长笔记?**
- A: 使用SemanticSplitterNodeParser或MarkdownNodeParser智能分块

**Q: 如何提高检索准确度?**
- A: 使用HybridRetriever结合向量和关键词检索,添加Reranker重排序

**Q: 如何减少存储开销?**
- A: 选择低维度embedding模型 (如384维本地模型)

**Q: 如何处理中文笔记?**
- A: 使用支持中文的embedding模型 (如sentence-transformers中文模型或OpenAI)

**Q: 如何批量重建索引?**
- A: 清空向量表,批量调用VectorStoreIndex.from_documents()

---

## 9. 参考资源

**官方文档**:
- llama-index文档: https://docs.llamaindex.ai/
- pgvector文档: https://github.com/pgvector/pgvector
- PostgreSQL文档: https://www.postgresql.org/docs/

**内部文档**:
- `框架选型.md` - llama-index选型理由
- `系统现状总结.md` - 当前实现状态
- `CLAUDE.md` - 开发最佳实践

**代码参考**:
- `services/llamaindex_service.py` - llama-index服务层
- `services/mcp_tools.py` - RAG工具定义
- `agents/task_igniter_langgraph.py` - Agent中RAG调用示例

---

**文档结束**
