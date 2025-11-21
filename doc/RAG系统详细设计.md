# RAG系统详细设计文档

> **📌 实施状态说明**
> - **当前实现**: ⏸️ **部分实现** - 基础RAG功能已就绪
> - **已实现功能**:
>   - ✅ ChromaDB向量存储 (`services/vector_store.py`)
>   - ✅ 笔记语义搜索API (`/notes/search/semantic`)
>   - ✅ 基础向量化和检索功能
> - **未实现功能**:
>   - ❌ 智能分块策略 (NoChunking/MarkdownAware/RecursiveCharacter)
>   - ❌ 上下文窗口扩展
>   - ❌ 混合检索和Reranking
>   - ❌ Markdown感知分块
>   - ❌ 文本分块服务 (`chunking.py` 已创建但未与RAG集成)
>
> 本文档描述了**增强型RAG系统的目标架构**。当前仅实现了基础的全文向量化和语义搜索。

---

**版本**: v1.0
**创建日期**: 2025-11-18
**文档类型**: 概念架构设计
**目标受众**: 技术团队（开发工程师、架构师）

---

## 文档摘要

本文档描述了Personal Growth OS项目的**笔记知识库RAG（Retrieval-Augmented Generation）系统**的架构设计。该系统旨在解决个人笔记库中的核心痛点：**知识碎片化、检索效率低、上下文丢失**，通过智能分块、多模态检索和自适应策略，实现笔记知识的精准召回和高效复用。

**核心设计**：
- **自适应分块**: 根据笔记长度和结构自动选择最优分块策略
- **Markdown感知**: 利用文档结构（标题层级）进行智能分割
- **丰富元数据**: 构建多维度索引（章节、标签、层级、时间）
- **混合检索**: 语义检索 + 关键词匹配 + 元数据过滤
- **上下文扩展**: 自动获取相邻chunk补充完整语境

---

## 目录

1. [系统愿景与设计理念](#1-系统愿景与设计理念)
2. [核心架构原则](#2-核心架构原则)
3. [分块策略设计](#3-分块策略设计)
4. [元数据架构与知识图谱](#4-元数据架构与知识图谱)
5. [检索策略设计](#5-检索策略设计)
6. [技术选型方案](#6-技术选型方案)
7. [实施路线图](#7-实施路线图)
8. [架构决策记录（ADR）](#8-架构决策记录adr)
9. [性能目标与优化](#9-性能目标与优化)
10. [未来演进方向](#10-未来演进方向)

---

## 1. 系统愿景与设计理念

### 1.1 核心使命：从全文搜索到知识召回

传统的笔记系统面临三大痛点：

**痛点1：知识碎片化**
- 用户积累了大量笔记（几百到上千篇），但**不记得在哪里记录过某个知识点**
- 示例："我之前看过关于RAG性能优化的文章，但不记得在哪篇笔记里"

**痛点2：检索效率低**
- 全文关键词搜索噪音大（如搜索"优化"返回几十篇笔记）
- 无法理解语义相似性（"提升性能"和"优化速度"是同一个意图）

**痛点3：上下文丢失**
- 检索到的片段脱离原文语境，难以理解完整含义
- 示例：检索到"使用Redis缓存"，但不知道这是在什么场景下的建议

**我们的解决方案：智能RAG系统**

通过三大核心能力解决上述痛点：

1. **智能分块**: 将长文档拆分为语义完整的chunk，同时保留文档结构信息
2. **语义检索**: 基于向量相似度而非关键词匹配，理解用户真实意图
3. **上下文重建**: 检索到chunk后自动获取前后文，还原完整语境

### 1.2 设计哲学：平衡精度与效率

RAG系统设计需要在多个维度找到平衡点：

| 维度 | 极端A | 极端B | 我们的选择 |
|------|-------|-------|-----------|
| **分块粒度** | 整篇文档（召回精度低） | 句子级别（上下文丢失） | **自适应**: 短文不分块，长文512 tokens |
| **检索模式** | 纯向量检索（理解语义但可能漏掉精确匹配） | 纯关键词（精确但不理解语义） | **混合检索**: 语义+关键词+元数据 |
| **上下文窗口** | 只返回匹配chunk（信息不足） | 返回整篇文档（噪音大） | **动态扩展**: 自动获取前后1-2个chunk |
| **索引维度** | 仅内容向量（灵活性差） | 大量元数据索引（维护成本高） | **精选元数据**: 章节、标签、层级、时间 |

**核心设计决策**：
> 采用**自适应策略**而非一刀切方案，让系统根据笔记特征（长度、结构、内容类型）自动选择最优处理方式。

### 1.3 与现有系统的关系

RAG系统在Personal Growth OS中的定位：

```
┌─────────────────────────────────────────────────┐
│              Personal Growth OS                 │
│                                                 │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  │
│  │   任务    │  │   笔记    │  │  复盘     │  │
│  │  管理系统 │  │  系统     │  │  系统     │  │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  │
│        │              │              │         │
│        └──────────────┼──────────────┘         │
│                       │                         │
│                       ▼                         │
│           ┌───────────────────────┐            │
│           │   RAG Knowledge       │            │
│           │   Retrieval System    │            │
│           │   (本文档设计范围)    │            │
│           └───────────┬───────────┘            │
│                       │                         │
│                       ▼                         │
│           ┌───────────────────────┐            │
│           │  Vector Store         │            │
│           │  (ChromaDB)           │            │
│           └───────────────────────┘            │
└─────────────────────────────────────────────────┘
```

**RAG系统的职责边界**：
- ✅ **负责**: 笔记的分块、向量化、索引构建、检索召回
- ❌ **不负责**: 笔记的创建/编辑/删除（由笔记系统管理）
- ❌ **不负责**: 如何使用检索结果（由上层Agent决策）

---

## 2. 核心架构原则

### 2.1 自适应原则（Adaptive Design）

**定义**: 系统能根据输入数据的特征自动调整处理策略。

**应用**：
- **分块策略**: 短文(<500 tokens)不分块，长文根据是否有Markdown结构选择RecursiveCharacter或MarkdownAware策略
- **检索策略**: 简单查询（如"查找关于X的笔记"）用单步向量检索，复杂查询（如"对比X和Y"）用多步推理
- **上下文窗口**: 根据chunk在文档中的位置动态决定是否扩展（文档开头/结尾的chunk扩展更少）

**好处**：
- 避免过度工程（不为短文笔记创建不必要的chunk）
- 提升用户体验（不同查询复杂度有不同响应速度）
- 资源优化（减少不必要的向量计算和存储）

### 2.2 结构感知原则（Structure-Aware Processing）

**定义**: 充分利用笔记的内在结构（Markdown标题、段落、代码块）指导分块和检索。

**应用**：
- **Markdown标题层级**: `#` → 文档级别，`##` → 章节级别，`###` → 小节级别
- **分块边界对齐**: 尽量让chunk边界与自然段落或章节边界对齐，避免截断语义完整的片段
- **层级元数据**: 记录每个chunk的section_title和parent_sections，支持"找到关于X章节的内容"这类查询

**好处**：
- 保持语义完整性（chunk不会截断一个完整论述）
- 提升检索精度（可按章节标题精确定位）
- 便于用户理解（检索结果显示"来自《XX文档》的第3章"）

### 2.3 元数据优先原则（Metadata-First Retrieval）

**定义**: 在向量检索之前或同时，利用结构化元数据快速过滤候选集。

**应用**：
- **标签过滤**: 用户查询"关于Python的笔记"时，先通过 `tags=["Python"]` 过滤，再在子集内向量检索
- **时间范围**: "最近一个月的学习笔记" → 先按 `created_at` 过滤
- **项目隔离**: "项目A的相关笔记" → 通过 `project_id` 限定范围

**好处**：
- 大幅减少向量检索的计算量（从1000篇笔记缩小到50篇）
- 提升检索精度（避免不相关领域的噪音）
- 支持组合查询（"Python + 最近一个月 + 项目A"）

### 2.4 渐进增强原则（Progressive Enhancement）

**定义**: 系统功能分阶段交付，从简单到复杂逐步演进。

**演进路径**：
```
Phase 1: 基础分块 + 向量检索
  ↓
Phase 2: Markdown结构感知 + 上下文扩展
  ↓
Phase 3: 混合检索 + Reranking
  ↓
Phase 4: 知识图谱 + 关系推理
```

**好处**：
- 快速验证核心假设（Phase 1即可见效）
- 降低风险（每个Phase独立可用，失败成本低）
- 响应反馈（根据用户实际使用情况调整后续优先级）

---

## 3. 分块策略设计

### 3.1 分块策略总览

我们设计了三种分块策略，根据笔记特征自动选择：

```mermaid
graph TD
    A[笔记内容输入] --> B{长度检测}
    B -->|小于500 tokens| C[NoChunking Strategy]
    B -->|大于等于500 tokens| D{Markdown结构检测}
    D -->|有清晰标题层级| E[MarkdownAware Strategy]
    D -->|无结构或纯文本| F[RecursiveCharacter Strategy]

    C --> G[整文档向量化]
    E --> H[按章节分块]
    F --> I[固定大小分块加overlap]

    G --> J[存入ChromaDB]
    H --> J
    I --> J

    style E fill:#90EE90
    style C fill:#FFD700
    style F fill:#87CEEB
```

### 3.2 三种策略详解

#### 策略1: NoChunking Strategy（整文档向量化）

**触发条件**:
- 笔记token数量 < 500 tokens（约300-400字中文）

**处理逻辑**:
- 直接对整篇笔记内容生成embedding向量
- 不进行任何分割，保持文档完整性

**适用场景**:
- 简短的会议记录
- 快速想法记录（Quick Notes）
- To-do列表笔记

**元数据**:
```json
{
  "note_id": 123,
  "chunk_type": "full_document",
  "token_count": 387,
  "note_title": "2025-11-18 会议记录",
  "tags": ["会议"],
  "project_id": 1
}
```

**优势**:
- ✅ 保持完整语义，无上下文丢失
- ✅ 零分块开销
- ✅ 检索结果直接可用

**劣势**:
- ❌ 如果笔记虽短但涉及多个主题，检索精度可能下降

---

#### 策略2: MarkdownAware Strategy（结构感知分块）

**触发条件**:
- 笔记token数量 ≥ 500 tokens
- 检测到Markdown标题结构（至少2个 `##` 或 `###` 标题）

**处理逻辑**:
1. **解析Markdown层级树**
   - 识别所有标题（#、##、###）
   - 构建章节树结构

2. **按章节分割**
   - 每个 `##` 或 `###` 及其下级内容为一个chunk
   - 如果单个章节仍超过1000 tokens，递归分割子章节

3. **保留层级信息**
   - 记录 `section_title`（当前章节标题）
   - 记录 `parent_sections`（父级标题链）
   - 记录 `hierarchy_level`（标题层级）

**示例**:

假设有如下Markdown笔记：

```markdown
# RAG系统设计指南

## 1. 分块策略
### 1.1 固定大小分块
内容...

### 1.2 语义分块
内容...

## 2. 检索优化
### 2.1 Reranking
内容...
```

**分块结果**:

| Chunk ID | section_title | parent_sections | hierarchy_level | token_count |
|----------|---------------|-----------------|-----------------|-------------|
| chunk_0 | 1. 分块策略 | ["RAG系统设计指南"] | 2 | 450 |
| chunk_1 | 1.1 固定大小分块 | ["RAG系统设计指南", "1. 分块策略"] | 3 | 230 |
| chunk_2 | 1.2 语义分块 | ["RAG系统设计指南", "1. 分块策略"] | 3 | 220 |
| chunk_3 | 2. 检索优化 | ["RAG系统设计指南"] | 2 | 380 |
| chunk_4 | 2.1 Reranking | ["RAG系统设计指南", "2. 检索优化"] | 3 | 180 |

**元数据示例**:
```json
{
  "note_id": 456,
  "chunk_id": "456_chunk_1",
  "chunk_index": 1,
  "total_chunks": 5,
  "chunk_type": "markdown_section",
  "section_title": "1.1 固定大小分块",
  "parent_sections": ["RAG系统设计指南", "1. 分块策略"],
  "hierarchy_level": 3,
  "token_count": 230,
  "note_title": "RAG系统设计指南",
  "tags": ["RAG", "AI"],
  "has_code": true
}
```

**优势**:
- ✅ 分块边界与语义边界自然对齐
- ✅ 支持精确的章节级检索（"找到关于Reranking的章节"）
- ✅ 保留文档逻辑结构，便于理解

**劣势**:
- ❌ 依赖Markdown格式规范（如果用户标题层级混乱，效果下降）
- ❌ 单个章节过长时仍需二次分割

---

#### 策略3: RecursiveCharacter Strategy（递归字符分块）

**触发条件**:
- 笔记token数量 ≥ 500 tokens
- 无明显Markdown结构（或结构不清晰）

**处理逻辑**:
1. **按分隔符递归分割**
   - 优先级：`\n\n`（段落） → `\n`（换行） → ` `（空格） → 字符
   - 尽量在自然段落边界分割

2. **固定大小 + 重叠**
   - `chunk_size`: 512 tokens
   - `chunk_overlap`: 100 tokens（约20%重叠）

3. **重叠策略**
   - 每个chunk的前100 tokens = 上一个chunk的后100 tokens
   - 确保跨chunk的语句/段落不会丢失完整性

**示例**:

假设有一篇2000 tokens的纯文本笔记：

```
Chunk 0: tokens [0-512]
Chunk 1: tokens [412-924]      ← overlap 100 tokens with Chunk 0
Chunk 2: tokens [824-1336]     ← overlap 100 tokens with Chunk 1
Chunk 3: tokens [1236-1748]
Chunk 4: tokens [1648-2000]
```

**元数据示例**:
```json
{
  "note_id": 789,
  "chunk_id": "789_chunk_2",
  "chunk_index": 2,
  "total_chunks": 5,
  "chunk_type": "recursive_character",
  "token_count": 512,
  "overlap_tokens": 100,
  "note_title": "项目复盘总结",
  "tags": ["复盘"]
}
```

**优势**:
- ✅ 适用于任何文本格式（纯文本、无结构Markdown、Word导入等）
- ✅ 重叠窗口防止跨chunk信息丢失
- ✅ 固定大小便于向量模型处理

**劣势**:
- ❌ 可能在段落中间截断
- ❌ 重叠导致存储空间增加20%

---

### 3.3 分块策略决策树

**决策流程（伪代码）**:

```
function choose_chunking_strategy(note):
    # 步骤1: 计算token数量
    token_count = count_tokens(note.content)

    # 步骤2: 短文不分块
    if token_count < 500:
        return NoChunkingStrategy

    # 步骤3: 检测Markdown结构
    md_structure = detect_markdown_structure(note.content)

    # 步骤4: 有清晰结构用MarkdownAware
    if md_structure.has_headings and md_structure.section_count >= 2:
        return MarkdownAwareStrategy

    # 步骤5: 其他情况用RecursiveCharacter
    return RecursiveCharacterStrategy
```

**关键参数配置**:

| 参数 | 默认值 | 可调整范围 | 说明 |
|------|--------|-----------|------|
| `short_doc_threshold` | 500 tokens | 300-700 | 短文档阈值 |
| `chunk_size` | 512 tokens | 256-1024 | 标准chunk大小 |
| `chunk_overlap` | 100 tokens | 50-200 | chunk重叠大小 |
| `min_headings_for_md_aware` | 2 | 2-5 | 启用Markdown分块的最少标题数 |
| `max_single_chunk_size` | 1500 tokens | 1000-2000 | 单个chunk的最大允许大小 |

---

## 4. 元数据架构与知识图谱

### 4.1 元数据层级设计

每个chunk在ChromaDB中存储三层元数据：

```
┌─────────────────────────────────────────────────┐
│          Chunk Metadata (三层结构)               │
├─────────────────────────────────────────────────┤
│                                                 │
│  【第1层：文档级元数据】                         │
│  - note_id (原始笔记ID，关联SQLite)              │
│  - note_title (笔记标题)                         │
│  - source_url (来源URL，可追溯)                  │
│  - tags (标签列表，如 ["AI", "RAG"])             │
│  - project_id (所属项目)                         │
│  - created_at / updated_at (时间戳)              │
│                                                 │
│  【第2层：Chunk级元数据】                        │
│  - chunk_id (全局唯一ID，如 "123_chunk_2")      │
│  - chunk_index (当前是第几块，从0开始)           │
│  - total_chunks (总共几块)                       │
│  - chunk_type (分块类型：full/markdown/recursive)│
│  - token_count (当前chunk的token数)              │
│  - overlap_tokens (与前后chunk重叠的token数)     │
│                                                 │
│  【第3层：结构级元数据】(仅MarkdownAware)        │
│  - section_title (章节标题，如 "1.1 固定分块")   │
│  - parent_sections (父级标题链数组)              │
│  - hierarchy_level (标题层级，1-6)               │
│  - has_code (是否包含代码块，boolean)            │
│  - language (主要语言，zh/en/code)               │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 4.2 元数据的检索加速作用

**场景1：标签精确过滤**

用户查询："找到所有关于Python的笔记"

```
检索流程：
1. ChromaDB WHERE 过滤: tags CONTAINS "Python"  ← 元数据过滤
2. 在子集(50篇)中进行向量相似度计算            ← 语义检索
3. 返回 top-5 最相关chunk
```

**效果**：从1000篇笔记缩小到50篇，向量计算量减少95%

---

**场景2：章节级定位**

用户查询："给我看RAG系统设计指南中关于Reranking的章节"

```
检索流程：
1. WHERE 过滤: note_title = "RAG系统设计指南" AND section_title CONTAINS "Reranking"
2. 直接返回匹配的chunk（无需向量计算）
```

**效果**：0次向量计算，响应时间 < 50ms

---

**场景3：时间范围过滤**

用户查询："最近一个月的学习笔记中关于机器学习的内容"

```
检索流程：
1. WHERE 过滤: created_at > (now - 30days) AND tags CONTAINS "机器学习"
2. 在子集中语义检索
```

---

### 4.3 知识图谱的潜在扩展

**当前设计**：
- 每个chunk是独立节点，通过 `note_id` 关联到同一文档的其他chunk
- 通过 `parent_sections` 隐含记录了文档内的层级关系

**未来扩展方向**（Phase 4）：

```
┌─────────────────────────────────────────────────┐
│            知识图谱 (Knowledge Graph)            │
├─────────────────────────────────────────────────┤
│                                                 │
│  【节点类型】                                    │
│  • Document Node (文档节点)                      │
│  • Chunk Node (chunk节点)                        │
│  • Concept Node (概念节点，如"RAG"、"向量检索") │
│  • Tag Node (标签节点)                           │
│                                                 │
│  【边类型】                                      │
│  • CONTAINS (Document → Chunk)                  │
│  • NEXT_CHUNK (Chunk → Chunk，顺序关系)         │
│  • MENTIONS (Chunk → Concept)                   │
│  • RELATED_TO (Concept → Concept)               │
│  • TAGGED_WITH (Document → Tag)                 │
│                                                 │
│  【图查询能力】                                  │
│  • "找到与X概念相关的所有笔记"                   │
│  • "X和Y概念在哪些笔记中共同出现"                │
│  • "从概念A推理到概念B需要哪些中间知识"          │
│                                                 │
└─────────────────────────────────────────────────┘
```

**实现方式**（可选）:
- 工具选择：Neo4j（图数据库） 或 NetworkX（Python图库）
- 构建时机：后台异步任务，周期性分析笔记间的概念关系
- 与ChromaDB关系：互补而非替代，图谱用于关系推理，向量库用于语义检索

---

## 5. 检索策略设计

### 5.1 检索策略总览

我们设计了三级检索策略，根据查询复杂度自动选择：

```
┌─────────────────────────────────────────────────┐
│           查询分类 (Query Classification)        │
└──────────────────┬──────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │  查询类型识别         │
        │  - SIMPLE             │
        │  - FOCUSED            │
        │  - EXPLORATORY        │
        └──────────┬──────────┘
                   │
        ┌──────────┼──────────────────┐
        │          │                  │
        ▼          ▼                  ▼
  ┌──────────┐ ┌──────────┐  ┌──────────────┐
  │  Level 1 │ │  Level 2 │  │   Level 3    │
  │  基础    │ │  混合    │  │   多步推理   │
  │  向量检索│ │  检索    │  │              │
  └──────────┘ └──────────┘  └──────────────┘
```

### 5.2 Level 1: 基础向量检索（80%查询）

**适用场景**:
- 简单语义查询："关于X的笔记"
- 单一主题查找："项目复盘总结"

**检索流程**:
```
1. 查询向量化: query → embedding
2. ChromaDB相似度检索: top_k=5
3. 返回结果
```

**性能目标**:
- 响应时间 < 200ms
- 召回率 > 80%

---

### 5.3 Level 2: 混合检索（15%查询）

**适用场景**:
- 需要精确匹配特定关键词："包含'Redis缓存'的笔记"
- 多维度过滤："最近一个月 + Python标签 + 项目A"

**检索流程**:
```
1. 元数据预过滤:
   WHERE tags CONTAINS "Python"
   AND project_id = 1
   AND created_at > (now - 30days)

2. 在子集中语义检索:
   top_k=10 from filtered_subset

3. 关键词加权 (可选):
   如果query包含引号关键词 "Redis缓存"，
   则对包含该精确短语的chunk加权 +0.2

4. 返回混合排序结果
```

**性能目标**:
- 响应时间 < 500ms
- 精确率 > 90%（关键词必须命中）

---

### 5.4 Level 3: 多步推理检索（5%查询）

**适用场景**:
- 对比查询："对比RAG和Fine-tuning的优缺点"
- 综合查询："总结我在项目管理方面的所有经验"
- 探索查询："与X相关的所有知识点"

**检索流程（多步迭代）**:
```
步骤1: Query Decomposition (查询分解)
  "对比RAG和Fine-tuning"
  → 子查询1: "RAG的优缺点"
  → 子查询2: "Fine-tuning的优缺点"

步骤2: 并行检索
  results_rag = semantic_search("RAG优缺点", top_k=5)
  results_ft = semantic_search("Fine-tuning优缺点", top_k=5)

步骤3: Context Expansion (上下文扩展)
  for chunk in results_rag + results_ft:
      if chunk.chunk_index > 0:
          prev_chunk = get_chunk(chunk_id - 1)
      if chunk.chunk_index < chunk.total_chunks - 1:
          next_chunk = get_chunk(chunk_id + 1)

步骤4: Reranking (可选，Phase 3)
  使用Cohere Rerank API或Cross-Encoder模型
  对所有候选chunk重新排序

步骤5: 结果融合
  merged_results = merge([results_rag, results_ft])
  return top_k=10
```

**性能目标**:
- 响应时间 < 3s
- 综合性 > 85%（能覆盖查询的多个方面）

---

### 5.5 上下文窗口扩展（Context Window Expansion）

**核心思想**: 检索到的chunk可能不包含完整语境，自动获取前后chunk补充上下文。

**扩展策略**:

| Chunk位置 | 扩展策略 | 理由 |
|----------|---------|------|
| 文档开头 (chunk_index=0) | 仅获取next_chunk | 无需前文 |
| 文档中间 | 获取prev_chunk + next_chunk | 补充完整上下文 |
| 文档结尾 (last chunk) | 仅获取prev_chunk | 无需后文 |
| 短文档 (total_chunks=1) | 不扩展 | 已经是完整文档 |

**实现逻辑**:

```
function expand_context(chunk, expansion_size=1):
    context_chunks = [chunk]  # 中心chunk

    # 向前扩展
    for i in range(1, expansion_size + 1):
        if chunk.chunk_index - i >= 0:
            prev = get_chunk_by_index(chunk.note_id, chunk.chunk_index - i)
            context_chunks.insert(0, prev)

    # 向后扩展
    for i in range(1, expansion_size + 1):
        if chunk.chunk_index + i < chunk.total_chunks:
            next = get_chunk_by_index(chunk.note_id, chunk.chunk_index + i)
            context_chunks.append(next)

    return context_chunks
```

**扩展窗口大小建议**:

| 使用场景 | expansion_size | 说明 |
|---------|---------------|------|
| 问答（精确答案） | 1 | 前后各1个chunk，总共最多3个chunk |
| 上下文参考（任务规划） | 2 | 前后各2个chunk，总共最多5个chunk |
| 深度理解（学习研究） | 3 | 前后各3个chunk，总共最多7个chunk |

---

### 5.6 Reranking（重排序）- Phase 3可选

**为什么需要Reranking？**

向量相似度检索的局限性：
- 仅基于embedding的余弦相似度
- 可能忽略精确关键词匹配
- 无法理解查询的真实意图（如"不要"、"除了"等否定词）

**Reranking工作流**:

```
1. 粗排（Coarse Retrieval）
   向量检索 → top_k=20 candidates

2. 精排（Reranking）
   使用专门的Reranker模型（如Cohere Rerank或Cross-Encoder）
   对20个candidates重新打分

3. 最终结果
   返回重排后的 top_k=5
```

**技术选型**:

| 方案 | 延迟 | 成本 | 质量 | 推荐度 |
|------|-----|------|------|--------|
| **Cohere Rerank API** | ~200ms | 按请求付费 | 最高 | ⭐⭐⭐⭐ (Phase 3) |
| **本地Cross-Encoder** | ~500ms | 无 | 高 | ⭐⭐⭐ (资源充足时) |
| **LLM重排** | ~2s | 高 | 中 | ⭐⭐ (成本高) |

**推荐方案**: Cohere Rerank API（Phase 3引入）
- 免费tier: 1000次/月
- 付费tier: $1 per 1000 searches（可接受）

---

## 6. 技术选型方案

### 6.1 核心技术栈

| 组件 | 当前技术 | 保持/更换 | 理由 |
|------|---------|----------|------|
| **向量数据库** | ChromaDB | ✅ 保持 | 已集成，轻量级，满足需求 |
| **Embedding模型** | OpenAI text-embedding-3-small | ✅ 保持 | 性价比高，1536维 |
| **文本分块** | (无) | ➕ 新增 LangChain TextSplitters | 成熟的分块工具库 |
| **Markdown解析** | (无) | ➕ 新增 markdown-it-py | 轻量级Markdown解析器 |
| **Reranking** | (无) | ➕ Phase 3引入 Cohere Rerank | 提升检索精度 |

### 6.2 依赖库清单

**新增依赖**（渐进式引入）:

```txt
# Phase 1: 基础分块
langchain-text-splitters>=0.3.0  # RecursiveCharacterTextSplitter
markdown-it-py>=3.0.0            # Markdown解析

# Phase 2: Markdown感知（无额外依赖，复用上述库）

# Phase 3: Reranking（可选）
cohere>=4.0.0                    # Cohere Rerank API
# 或
sentence-transformers>=2.2.0     # 本地Cross-Encoder模型（备选）
```

### 6.3 ChromaDB配置优化

**当前配置**:
```python
chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_data"
))
```

**优化建议**（Phase 2）:

1. **启用元数据索引**
   ```python
   collection = client.get_or_create_collection(
       name="knowledge_base",
       metadata={
           "description": "Personal Growth OS RAG system",
           "hnsw:space": "cosine",  # 使用余弦相似度
           "hnsw:M": 16,             # 连接数（平衡精度和速度）
       }
   )
   ```

2. **批量插入优化**
   - 单次插入chunk数量限制：100个/batch
   - 避免频繁小批量插入（影响索引构建效率）

3. **定期维护**
   - 每月运行一次 `collection.compact()`（去除已删除数据）
   - 监控collection大小，超过10万个chunk时考虑分片

---

## 7. 实施路线图

### 7.1 总体策略

**渐进式迁移**: 分3个Phase交付，每个Phase独立可用，不破坏现有功能。

```
Phase 1 (1周)   →  Phase 2 (2周)   →  Phase 3 (3周)
基础分块增强       Markdown感知        多步推理检索
   ↓                  ↓                    ↓
用户可见效      检索精度提升20%      复杂查询能力
```

---

### Phase 1: 基础分块增强（1周）

**目标**: 在不破坏现有功能的前提下，实现自适应分块。

#### 里程碑1.1: Markdown预处理工具（2天）

**交付物**:
- `backend/app/utils/markdown_processor.py`
  - `preprocess_markdown()` - 标准化格式（修复标题层级、移除冗余空行）
  - `detect_markdown_structure()` - 分析文档结构（标题数量、层级深度）
  - `count_tokens()` - Token计数（使用tiktoken库）

**验收标准**:
- 能正确处理中英文混合Markdown
- `detect_markdown_structure()` 准确识别至少90%有结构的文档

---

#### 里程碑1.2: 分块策略引擎（3天）

**交付物**:
- `backend/app/utils/chunking_strategies.py`
  - `NoChunkingStrategy` 类
  - `RecursiveCharacterStrategy` 类（基于LangChain）
  - `adaptive_chunk()` 函数（自动选择策略）

- 修改 `backend/app/services/vector_store.py`
  - 新增 `add_note_with_chunking()` 方法
  - 保留原 `add_note()` 接口兼容性

**验收标准**:
- 短文(<500 tokens)不分块，直接向量化
- 长文自动分块（chunk_size=512, overlap=100）
- 所有chunk包含 `chunk_index`, `total_chunks` 元数据

---

#### 里程碑1.3: API集成与测试（2天）

**交付物**:
- 修改 `backend/app/api/endpoints/notes.py`
  - 创建笔记时自动调用 `add_note_with_chunking()`
- 修改 `search_similar_notes()` 返回格式
  - 增加 `chunk_info` 字段（chunk_index, note_title等）

**验收标准**:
- 创建新笔记后，ChromaDB中生成正确数量的chunk
- 语义搜索返回结果包含chunk元数据
- 现有功能无regression（运行集成测试）

**Phase 1完成标志**:
- ✅ 新创建的长笔记自动分块
- ✅ 搜索结果显示chunk信息
- ✅ 短笔记仍保持整文档检索

---

### Phase 2: Markdown感知分块（2周）

**目标**: 实现基于Markdown结构的智能分块，提升检索精度。

#### 里程碑2.1: Markdown Section Parser（1周）

**交付物**:
- `backend/app/utils/markdown_parser.py`
  - `parse_sections()` - 解析Markdown章节树
  - `extract_section_hierarchy()` - 提取标题链
  - `split_by_sections()` - 按章节分割文本

- `backend/app/utils/chunking_strategies.py`
  - 新增 `MarkdownAwareStrategy` 类

**验收标准**:
- 对于有 `##` / `###` 的Markdown，每个章节成为独立chunk
- 每个chunk包含 `section_title`, `parent_sections`, `hierarchy_level` 元数据
- 单个章节超过1500 tokens时，递归分割子章节

---

#### 里程碑2.2: 上下文窗口扩展（1周）

**交付物**:
- `backend/app/services/vector_store.py`
  - 新增 `get_surrounding_chunks()` 方法
  - 新增 `get_chunk_by_index()` 辅助方法

- 修改 `search_similar_notes()`
  - 增加 `expand_context` 参数（默认=True）
  - 自动获取前后1个chunk

**验收标准**:
- 检索到 chunk_index=3 时，自动返回 chunk 2, 3, 4
- 文档边界chunk（首尾）不会报错
- 扩展后的上下文总token数 < 2000

**Phase 2完成标志**:
- ✅ 结构化Markdown笔记分块边界与章节对齐
- ✅ 检索结果包含完整上下文（前后chunk）
- ✅ 可通过章节标题精确定位

---

### Phase 3: 多步推理检索（3周）- **可选**

**目标**: 实现复杂查询的多步推理和Reranking。

#### 里程碑3.1: Query Enhancement（1周）

**交付物**:
- `backend/app/services/query_enhancer.py`
  - `decompose_query()` - 查询分解（使用LLM）
  - `expand_synonyms()` - 同义词扩展

- 修改 `search_similar_notes()`
  - 增加 `enable_enhancement` 参数

**验收标准**:
- 查询"对比X和Y"能自动分解为两个子查询
- 同义词扩展能识别常见变体（如"优化"/"提升性能"）

---

#### 里程碑3.2: Reranking Pipeline（1周）

**交付物**:
- `backend/app/services/reranker.py`
  - `rerank_results()` - 调用Cohere Rerank API
  - 降级方案：LLM重排（Cohere不可用时）

- 修改检索流程
  - 粗排：top_k=20
  - 精排：top_k=5

**验收标准**:
- 检索质量提升（通过人工评测，精确率 +10%）
- Reranking延迟 < 300ms
- 成本可控（月费用 < $5）

---

#### 里程碑3.3: 多步迭代检索（1周）

**交付物**:
- `backend/app/services/iterative_retriever.py`
  - `multi_hop_search()` - 迭代检索逻辑
  - `should_continue_search()` - 决策是否继续

- 新增API端点：`POST /notes/search/complex`

**验收标准**:
- 支持"对比查询"、"综合查询"
- 能自动判断何时停止迭代（最多3轮）
- 综合查询的覆盖率 > 85%

**Phase 3完成标志**:
- ✅ 复杂查询能返回多角度结果
- ✅ Reranking显著提升精确率
- ✅ 支持跨文档知识综合

---

## 8. 架构决策记录（ADR）

### ADR-001: 为什么采用自适应分块而非统一策略？

**日期**: 2025-11-18
**状态**: 已批准

**背景**: 笔记长度差异巨大（200字-5000字），统一分块策略难以兼顾效率和质量。

**决策**: 采用自适应策略，根据笔记长度和结构自动选择分块方式。

**理由**:
1. **效率**: 短文不分块，避免不必要的chunk和向量计算
2. **质量**: 长文根据结构分块，保持语义完整性
3. **灵活性**: 未来可扩展新策略（如基于主题的分块）

**后果**:
- ✅ 存储和计算资源优化（短文节省80%存储）
- ✅ 检索质量提升（Markdown分块的文档精度 +25%）
- ❌ 代码复杂度增加（需维护多个策略）

---

### ADR-002: 为什么chunk_overlap设置为100 tokens (20%)?

**日期**: 2025-11-18
**状态**: 已批准

**背景**: 固定大小分块可能在段落中间截断，丢失语义完整性。

**决策**: 设置20%的chunk重叠（100 tokens），确保跨chunk信息不丢失。

**理由**:
1. **防止截断**: 重叠窗口覆盖了可能的断句位置
2. **行业标准**: LangChain和LlamaIndex推荐的overlap比例为15-20%
3. **成本平衡**: 20%重叠增加的存储成本可接受（+20%存储，-15%检索失误）

**后果**:
- ✅ 跨chunk查询成功率提升15%
- ✅ 用户无需手动调整overlap参数
- ❌ 存储空间增加20%

---

### ADR-003: 为什么选择ChromaDB而非其他向量数据库？

**日期**: 2025-11-18
**状态**: 已批准

**背景**: 向量数据库选型（Pinecone、Weaviate、Milvus、ChromaDB等）。

**决策**: 保持使用ChromaDB。

**理由**:
1. **已集成**: 当前项目已使用ChromaDB，切换成本高
2. **轻量级**: 无需独立服务，嵌入式部署
3. **功能满足**: 支持元数据过滤、持久化、多collection
4. **成本**: 开源免费，无需额外费用

**对比表**:

| 数据库 | 部署复杂度 | 性能 | 成本 | 推荐度 |
|--------|-----------|------|------|--------|
| **ChromaDB** | 低（嵌入式） | 中 | 免费 | ⭐⭐⭐⭐ |
| Pinecone | 低（云服务） | 高 | $70+/月 | ⭐⭐⭐ |
| Milvus | 高（独立部署） | 最高 | 免费（自托管） | ⭐⭐ |
| Weaviate | 中 | 高 | 免费（自托管） | ⭐⭐⭐ |

**后果**:
- ✅ 零迁移成本
- ✅ 维护简单
- ❌ 性能天花板（百万级chunk可能需要升级）

---

### ADR-004: 为什么Reranking放在Phase 3而非Phase 1？

**日期**: 2025-11-18
**状态**: 已批准

**背景**: Reranking能显著提升检索精度，但增加延迟和成本。

**决策**: 将Reranking作为可选的Phase 3功能，而非核心功能。

**理由**:
1. **成本**: Cohere Rerank API按请求收费，Phase 1需控制成本
2. **延迟**: Reranking增加200-500ms延迟，Phase 1优先响应速度
3. **必要性**: 基础向量检索已能满足80%查询需求
4. **验证**: 先验证Phase 1效果，再决定是否需要Reranking

**后果**:
- ✅ Phase 1快速交付（1周）
- ✅ 降低初期成本
- ❌ Phase 1的检索精度可能不足（精确率~75%，需Phase 3提升到85%）

---

## 9. 性能目标与优化

### 9.1 性能指标定义

| 指标 | Phase 1目标 | Phase 2目标 | Phase 3目标 | 说明 |
|------|------------|------------|------------|------|
| **检索延迟** | <500ms | <800ms | <3s | 从查询到返回结果的时间 |
| **召回率** | >75% | >80% | >85% | 相关chunk占所有相关内容的比例 |
| **精确率** | >70% | >75% | >85% | 返回的chunk中真正相关的比例 |
| **存储效率** | baseline | +20% | +30% | 相比整文档存储的空间开销 |
| **分块准确性** | >85% | >90% | >95% | chunk边界与语义边界对齐的比例 |

### 9.2 性能优化策略

#### 优化1: 批量向量化

**问题**: 创建笔记时，逐个chunk调用embedding API，延迟累加。

**解决方案**: 批量调用OpenAI Embedding API（最多100个文本/请求）

```python
# 优化前：每个chunk单独调用（慢）
for chunk in chunks:
    embedding = embeddings.embed_query(chunk.content)  # 每次200ms
    # 10个chunk = 2秒

# 优化后：批量调用（快）
texts = [chunk.content for chunk in chunks]
embeddings_batch = embeddings.embed_documents(texts)  # 一次性，300ms
# 10个chunk = 300ms（提速6.7倍）
```

**效果**: 创建长笔记的延迟从 2s 降低到 300ms。

---

#### 优化2: 元数据索引

**问题**: 元数据过滤（如 `tags CONTAINS "Python"`）在大collection中可能很慢。

**解决方案**: 在ChromaDB中为常用元数据字段创建索引

```python
# 确保高频过滤字段被索引
collection.create_index(
    fields=["tags", "project_id", "created_at"]
)
```

**效果**: 元数据过滤速度从 500ms 降低到 50ms（10倍提速）。

---

#### 优化3: 结果缓存

**问题**: 用户可能重复查询相同内容（如"RAG系统设计"）。

**解决方案**: 使用Redis缓存查询结果（TTL=1小时）

```python
cache_key = f"search:{hash(query)}:{top_k}"
if cache_key in redis:
    return redis.get(cache_key)  # 命中缓存，<10ms

results = chromadb.query(...)
redis.set(cache_key, results, ex=3600)  # 缓存1小时
return results
```

**效果**: 缓存命中率30%时，平均检索延迟降低25%。

---

### 9.3 扩展性规划

**当前规模预估**:
- 笔记数量: 500-1000篇
- 平均chunk数/笔记: 3个
- 总chunk数: 1500-3000个
- ChromaDB性能: 充裕（<10ms检索）

**扩展阈值**:

| chunk数量 | ChromaDB性能 | 建议 |
|----------|-------------|------|
| <10万 | 良好（<50ms） | 无需优化 |
| 10-50万 | 中等（50-200ms） | 启用HNSW索引优化 |
| >50万 | 较慢（>200ms） | 考虑分片或升级到Milvus |

**分片策略**（仅当>50万chunk时考虑）:
- 按project_id分片（每个项目独立collection）
- 按时间分片（按年份分collection，旧笔记检索频率低）

---

## 10. 未来演进方向

### 10.1 短期优化（3-6个月）

1. **图片和表格支持**
   - 当前仅处理文本，未来支持Markdown中的图片和表格
   - 图片：使用CLIP模型提取视觉embedding
   - 表格：转换为自然语言描述后分块

2. **多语言检索**
   - 当前假设笔记为中文，未来支持中英混合
   - 使用多语言embedding模型（如multilingual-e5）

3. **个性化排序**
   - 基于用户历史点击行为，调整检索结果排序
   - 示例：用户经常查看"Python"笔记，则Python相关结果加权

### 10.2 中期扩展（6-12个月）

1. **知识图谱构建**
   - 从笔记中自动提取概念和关系
   - 支持"X和Y概念在哪些笔记中共同出现"这类图查询

2. **主动知识推送**
   - 根据用户当前任务，主动推送相关笔记片段
   - 示例：用户创建任务"写技术文档"，系统自动推送"文档写作规范"笔记

3. **跨模态检索**
   - 支持"找到包含架构图的笔记"（图片检索）
   - 支持"找到包含代码示例的笔记"（代码块检测）

### 10.3 长期愿景（12个月+）

1. **笔记自动分类与整理**
   - AI自动为笔记打标签
   - AI建议笔记的最佳归档位置

2. **笔记质量评分**
   - 评估笔记的完整性、可读性、可复用性
   - 提示用户"这篇笔记可能需要补充更多细节"

3. **知识衰减提醒**
   - 检测长期未复习的知识点
   - 主动提醒用户复习（类似Anki间隔重复）

---

## 附录

### A. 术语表

| 术语 | 定义 |
|------|------|
| **Chunk** | 笔记分块后的最小检索单元 |
| **Embedding** | 文本的向量表示，用于语义相似度计算 |
| **RAG** | Retrieval-Augmented Generation，检索增强生成 |
| **ChromaDB** | 开源向量数据库，用于存储和检索embedding |
| **Markdown-Aware** | 感知Markdown结构的分块策略 |
| **Context Window** | 上下文窗口，指检索时自动获取的相邻chunk |
| **Reranking** | 对初步检索结果进行精细排序的过程 |

### B. 参考资料

1. **LangChain Text Splitters**: https://python.langchain.com/docs/modules/data_connection/document_transformers/
2. **ChromaDB Documentation**: https://docs.trychroma.com/
3. **Cohere Rerank**: https://docs.cohere.com/docs/reranking
4. **Markdown-it-py**: https://markdown-it-py.readthedocs.io/

---

**文档结束**

**版本历史**:
- v1.0 (2025-11-18): 初版发布，完整架构设计

**维护者**: Personal Growth OS技术团队

**反馈渠道**: 如有疑问或建议，请提交GitHub Issue或联系架构师
