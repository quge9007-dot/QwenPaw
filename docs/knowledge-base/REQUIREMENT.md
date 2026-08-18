# QwenPaw 知识库模块 — 需求设计文档

> 版本：v1.0 | 日期：2026-08-18 | 作者：DTCoder
> 状态：Draft

---

## 目录

1. [概述与背景](#1-概述与背景)
2. [功能需求](#2-功能需求)
3. [架构设计](#3-架构设计)
4. [数据模型](#4-数据模型)
5. [API 设计](#5-api-设计)
6. [与现有系统集成](#6-与现有系统集成)
7. [非功能需求](#7-非功能需求)
8. [实现路线图](#8-实现路线图)
9. [风险与待决议题](#9-风险与待决议题)

---

## 1. 概述与背景

### 1.1 定位

QwenPaw 知识库模块是个人 AI 助手平台的核心能力之一，旨在让用户将个人文档、笔记、网页、对话记录等异构信息**结构化存储、语义化检索、智能化复用**，使 Agent 能够在对话中主动引用相关知识，实现"越用越聪明"。

### 1.2 当前状态

| 维度 | 现有能力 | 差距 |
|------|---------|------|
| 文件搜索 | `file_search` (grep + glob) 基于关键词 | 无语义理解，不支持跨文档检索 |
| 记忆系统 | ADBPG / RemeLight 记忆管理 | 面向对话记忆，非文档知识 |
| 上下文 | `light_context_manager` 对话压缩 | 不注入外部知识 |
| 文档处理 | PDF/Office Skills（docx/pdf/pptx/xlsx） | 仅限单次操作，无持久化索引 |

### 1.3 目标用户场景

| 场景 | 描述 | 优先级 |
|------|------|:------:|
| 研究学习 | 收集论文、技术文章，随时检索和提问 | P0 |
| 个人笔记 | 日常笔记、灵感记录，按主题聚合 | P0 |
| 项目知识 | 项目文档、代码片段、设计决策记录 | P1 |
| 对话归档 | 将与 Agent 的对话摘要存入知识库 | P1 |
| 团队共享 | 在团队空间中共享知识条目 | P2 |

---

## 2. 功能需求

### 2.1 知识摄取（Ingestion）

| ID | 功能 | 描述 | 优先级 |
|----|------|------|:------:|
| KB-001 | 文件上传 | 支持 PDF、Word、Markdown、TXT、HTML、CSV 等格式 | P0 |
| KB-002 | URL 抓取 | 输入 URL 自动抓取网页内容并解析 | P0 |
| KB-003 | 文本直接录入 | 用户直接粘贴/输入文本 | P0 |
| KB-004 | 对话保存 | 一键将当前对话摘要存入知识库 | P1 |
| KB-005 | 批量导入 | 支持 ZIP 包或目录批量导入 | P1 |
| KB-006 | 邮件/消息导入 | 从频道消息中提取知识 | P2 |

### 2.2 知识处理（Processing）

| ID | 功能 | 描述 | 优先级 |
|----|------|------|:------:|
| KB-010 | 文档解析 | 提取文本、表格、图片描述 | P0 |
| KB-011 | 智能分块 | 按语义边界分块（段落/章节），支持滑动窗口 | P0 |
| KB-012 | 向量化 | 调用 Embedding 模型生成向量 | P0 |
| KB-013 | 元数据提取 | 自动提取标题、作者、日期、关键词 | P0 |
| KB-014 | 去重检测 | 基于内容哈希或语义相似度去重 | P1 |
| KB-015 | 摘要生成 | 为长文档自动生成摘要 | P1 |
| KB-016 | 多语言处理 | 自动检测语言并选择合适的分词/Embedding 策略 | P1 |

### 2.3 知识组织（Organization）

| ID | 功能 | 描述 | 优先级 |
|----|------|------|:------:|
| KB-020 | 集合管理 | 创建/删除/重命名集合（Collection），类比文件夹 | P0 |
| KB-021 | 标签系统 | 为知识条目打标签，支持多标签筛选 | P0 |
| KB-022 | 分类管理 | 自动分类 + 手动分类 | P1 |
| KB-023 | 知识图谱 | 条目间关联（引用、相似、相关） | P2 |
| KB-024 | 置顶/收藏 | 标记重要条目 | P1 |

### 2.4 知识检索（Retrieval）

| ID | 功能 | 描述 | 优先级 |
|----|------|------|:------:|
| KB-030 | 语义搜索 | 基于向量相似度的自然语言搜索 | P0 |
| KB-031 | 关键词搜索 | 基于 BM25 / 全文索引的精确匹配 | P0 |
| KB-032 | 混合搜索 | 语义 + 关键词融合排序 | P0 |
| KB-033 | 过滤搜索 | 按集合、标签、日期范围、文件类型过滤 | P0 |
| KB-034 | RAG 问答 | 检索后由 LLM 生成答案，带引用来源 | P0 |
| KB-035 | 浏览模式 | 按集合/标签树形浏览 | P1 |

### 2.5 知识管理（Management）

| ID | 功能 | 描述 | 优先级 |
|----|------|------|:------:|
| KB-040 | 条目 CRUD | 查看、编辑、删除知识条目 | P0 |
| KB-041 | 版本管理 | 知识条目更新时保留历史版本 | P2 |
| KB-042 | 导出 | 导出为 Markdown/PDF/JSON | P1 |
| KB-043 | 统计面板 | 知识库容量、条目数、检索统计 | P2 |
| KB-044 | 回收站 | 软删除 + 恢复机制 | P1 |

### 2.6 Agent 集成

| ID | 功能 | 描述 | 优先级 |
|----|------|------|:------:|
| KB-050 | 自动检索 | Agent 对话时自动检索相关知识 | P0 |
| KB-051 | 检索工具 | 暴露 `knowledge_search` Tool 供 Agent 调用 | P0 |
| KB-052 | 知识注入 | 检索结果注入 Agent 上下文 | P0 |
| KB-053 | 主动推荐 | 根据对话主题推荐相关知识 | P1 |
| KB-054 | 知识沉淀 | Agent 主动将对话中有价值的信息存入知识库 | P2 |

---

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    QwenPaw Agent                      │
│  ┌──────────┐  ┌──────────┐  ┌───────────────────┐   │
│  │  Memory   │  │ Context  │  │  Knowledge Base   │   │
│  │  System   │  │ Manager  │  │  (NEW)            │   │
│  └──────────┘  └──────────┘  └────────┬──────────┘   │
└───────────────────────────────────────┼──────────────┘
                                        │
         ┌──────────────────────────────┼──────────────────────────────┐
         │                     Knowledge Base Module                    │
         │                                                               │
         │  ┌──────────────┐  ┌──────────────┐  ┌───────────────────┐   │
         │  │  Ingestion   │  │  Processing  │  │    Retrieval      │   │
         │  │  Pipeline    │  │  Pipeline    │  │    Engine         │   │
         │  │              │  │              │  │                   │   │
         │  │ • File Load  │  │ • Parse      │  │ • Semantic Search │   │
         │  │ • URL Fetch  │  │ • Chunk      │  │ • Keyword Search  │   │
         │  │ • Text Input │  │ • Embed      │  │ • Hybrid Search   │   │
         │  │ • Batch      │  │ • Index      │  │ • RAG Pipeline    │   │
         │  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘   │
         │         │                 │                    │              │
         │         └─────────────────┼────────────────────┘              │
         │                           │                                   │
         │  ┌────────────────────────┼───────────────────────────────┐   │
         │  │                  Storage Layer                          │   │
         │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐  │   │
         │  │  │  Vector  │  │   Full-  │  │   Metadata Store     │  │   │
         │  │  │  Store   │  │   Text   │  │   (SQLite / ADBPG)   │  │   │
         │  │  │ (Chroma/ │  │  Index   │  │                      │  │   │
         │  │  │  Milvus/ │  │ (SQLite  │  │  • Collections       │  │   │
         │  │  │  FAISS)  │  │  FTS5)   │  │  • Tags              │  │   │
         │  │  └──────────┘  └──────────┘  │  • Versions          │  │   │
         │  │                              └──────────────────────┘  │   │
         │  └────────────────────────────────────────────────────────┘   │
         │                                                               │
         │  ┌──────────────────────────────────────────────────────┐     │
         │  │                   API Layer                           │     │
         │  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │     │
         │  │  │  REST API    │  │  Agent Tool  │  │  Skill     │  │     │
         │  │  │  (FastAPI)   │  │  Interface   │  │  Interface │  │     │
         │  │  └──────────────┘  └──────────────┘  └────────────┘  │     │
         │  └──────────────────────────────────────────────────────┘     │
         └──────────────────────────────────────────────────────────────┘
```

### 3.2 模块划分

| 模块 | 路径 | 职责 |
|------|------|------|
| `kb_core` | `src/qwenpaw/knowledge_base/` | 核心抽象与接口定义 |
| `kb_ingestion` | `src/qwenpaw/knowledge_base/ingestion/` | 文档加载、URL 抓取、文本输入 |
| `kb_processing` | `src/qwenpaw/knowledge_base/processing/` | 解析、分块、向量化、索引 |
| `kb_retrieval` | `src/qwenpaw/knowledge_base/retrieval/` | 语义搜索、关键词搜索、混合搜索、RAG |
| `kb_store` | `src/qwenpaw/knowledge_base/store/` | 向量存储、全文索引、元数据存储 |
| `kb_api` | `src/qwenpaw/knowledge_base/api/` | REST 路由 + Agent Tool 定义 |
| `kb_skill` | `src/qwenpaw/agents/skills/knowledge-base/` | 知识库 Skill（SKILL.md + 脚本） |

### 3.3 技术选型建议

| 组件 | 方案 A（轻量/本地） | 方案 B（高性能/扩展） | 推荐 |
|------|-------------------|---------------------|:----:|
| 向量存储 | ChromaDB（嵌入式） | Milvus Lite / Qdrant | A（本地优先） |
| 全文索引 | SQLite FTS5 | Elasticsearch | A |
| Embedding | BGE-small / all-MiniLM | 云端 Embedding API | A（隐私优先） |
| 文档解析 | 复用现有 Office Skills | Unstructured / LlamaParse | A（复用） |
| 元数据存储 | SQLite | ADBPG（复用现有） | A → B |

---

## 4. 数据模型

### 4.1 核心实体

```
KnowledgeBase
├── id: str (UUID)
├── name: str
├── description: str
├── owner_id: str
├── created_at: datetime
└── updated_at: datetime

Collection (集合)
├── id: str (UUID)
├── kb_id: str (FK → KnowledgeBase)
├── name: str
├── parent_id: str (nullable, 支持嵌套)
├── description: str
├── created_at: datetime
└── updated_at: datetime

KnowledgeEntry (知识条目)
├── id: str (UUID)
├── collection_id: str (FK → Collection)
├── title: str
├── content: str (原始文本)
├── content_hash: str (SHA256，去重用)
├── source_type: enum (file / url / text / conversation)
├── source_uri: str (nullable, 原始来源)
├── file_type: str (nullable, pdf/docx/md/...)
├── chunk_count: int
├── metadata: JSON (作者、日期、关键词等)
├── status: enum (processing / ready / error)
├── created_at: datetime
└── updated_at: datetime

Chunk (分块)
├── id: str (UUID)
├── entry_id: str (FK → KnowledgeEntry)
├── chunk_index: int
├── content: str
├── token_count: int
├── embedding: vector (float[])
├── metadata: JSON (章节标题、页码等)
└── created_at: datetime

Tag (标签)
├── id: str (UUID)
├── kb_id: str (FK → KnowledgeBase)
├── name: str
└── color: str (nullable)

EntryTag (条目-标签关联)
├── entry_id: str (FK → KnowledgeEntry)
└── tag_id: str (FK → Tag)
```

### 4.2 存储策略

| 数据 | 存储引擎 | 说明 |
|------|---------|------|
| 元数据（实体/集合/标签） | SQLite / ADBPG | 结构化数据，需要事务和关联查询 |
| 向量（Embedding） | ChromaDB / FAISS | 高维向量，需要 ANN 检索 |
| 全文索引 | SQLite FTS5 | 关键词搜索，BM25 排序 |
| 原始文件 | 文件系统 | 用户上传的原始文件备份 |

---

## 5. API 设计

### 5.1 REST API（FastAPI Router）

#### 知识库管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/kb` | 创建知识库 |
| GET | `/api/kb` | 列出知识库 |
| GET | `/api/kb/{kb_id}` | 获取知识库详情 |
| DELETE | `/api/kb/{kb_id}` | 删除知识库 |
| GET | `/api/kb/{kb_id}/stats` | 知识库统计 |

#### 集合管理

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/kb/{kb_id}/collections` | 创建集合 |
| GET | `/api/kb/{kb_id}/collections` | 列出集合 |
| PUT | `/api/kb/{kb_id}/collections/{col_id}` | 更新集合 |
| DELETE | `/api/kb/{kb_id}/collections/{col_id}` | 删除集合 |

#### 知识条目

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/kb/{kb_id}/entries` | 创建知识条目（文本/URL） |
| POST | `/api/kb/{kb_id}/entries/upload` | 上传文件创建条目 |
| GET | `/api/kb/{kb_id}/entries` | 列出条目（支持分页/过滤） |
| GET | `/api/kb/{kb_id}/entries/{entry_id}` | 获取条目详情 |
| PUT | `/api/kb/{kb_id}/entries/{entry_id}` | 更新条目 |
| DELETE | `/api/kb/{kb_id}/entries/{entry_id}` | 删除条目 |

#### 检索

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/kb/{kb_id}/search` | 语义/关键词/混合搜索 |
| POST | `/api/kb/{kb_id}/ask` | RAG 问答 |

#### 标签

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/api/kb/{kb_id}/tags` | 创建标签 |
| GET | `/api/kb/{kb_id}/tags` | 列出标签 |
| PUT | `/api/kb/{kb_id}/tags/{tag_id}` | 更新标签 |
| DELETE | `/api/kb/{kb_id}/tags/{tag_id}` | 删除标签 |

### 5.2 Agent Tool 接口

```python
# knowledge_search — Agent 可调用的检索工具
@tool
async def knowledge_search(
    query: str,
    kb_id: str | None = None,
    collection_id: str | None = None,
    search_type: Literal["semantic", "keyword", "hybrid"] = "hybrid",
    top_k: int = 5,
    filters: dict | None = None,
) -> ToolResponse:
    """搜索知识库，返回最相关的知识条目片段。"""

# knowledge_add — Agent 可调用的添加工具
@tool
async def knowledge_add(
    content: str,
    title: str,
    kb_id: str | None = None,
    collection_id: str | None = None,
    tags: list[str] | None = None,
) -> ToolResponse:
    """将文本内容添加到知识库。"""

# knowledge_list — Agent 可调用的浏览工具
@tool
async def knowledge_list(
    kb_id: str | None = None,
    collection_id: str | None = None,
    tag: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> ToolResponse:
    """列出知识库中的条目。"""
```

### 5.3 检索请求/响应示例

```json
// POST /api/kb/{kb_id}/search
{
  "query": "QwenPaw 的插件架构是怎样的？",
  "search_type": "hybrid",
  "top_k": 5,
  "filters": {
    "collection_id": "col-xxx",
    "tags": ["技术文档"],
    "date_from": "2026-01-01"
  }
}

// Response
{
  "results": [
    {
      "entry_id": "entry-xxx",
      "title": "QwenPaw 插件系统设计",
      "chunk_content": "...插件架构采用分层设计...",
      "score": 0.92,
      "metadata": {
        "source": "docs/architecture.md",
        "page": 3,
        "chunk_index": 2
      }
    }
  ],
  "total": 42,
  "search_time_ms": 85
}
```

---

## 6. 与现有系统集成

### 6.1 与 Memory 系统集成

```
Conversation → Memory Manager
                    │
                    ├── 对话摘要 → KnowledgeBase (KB-004)
                    │
                    └── 检索上下文 ← KnowledgeBase (KB-050)
```

- 知识库条目可以作为 Memory 的扩展存储
- 对话记忆和知识库记忆可在检索时融合排序
- 复用 `base_memory_manager.py` 的抽象接口设计

### 6.2 与 Context 系统集成

```
Agent Context
├── System Prompt
├── Conversation History (compressed)
├── Tool Results
└── Knowledge Context ← NEW
    ├── Auto-retrieved chunks
    └── Agent-triggered search results
```

- 在 `agent_context.py` 中新增 `knowledge_context` 字段
- 检索结果自动注入，与现有 `light_context_manager` 协作

### 6.3 与 Skill 系统集成

```
skills/knowledge-base/
├── SKILL.md          # 技能描述（Agent 可见）
├── SKILL.zh.md       # 中文版
└── scripts/
    ├── search.py     # 检索脚本
    ├── add.py        # 添加脚本
    └── manage.py     # 管理脚本
```

- 遵循现有 Skill 结构（参考 `skills/docx-zh/`）
- 支持 `skill_load("knowledge-base")` 动态加载

### 6.4 与文件系统工具集成

- 复用 `file_search.py` 的文件类型判断逻辑
- 复用 `file_io.py` 的文件读写和路径解析
- 新建文件时自动触发知识库索引（可选配置）

### 6.5 与安全系统集成

- 复用 `security/` 模块的访问控制
- 知识库维度支持 `access_control` 策略
- 文件上传复用已有的安全扫描机制

---

## 7. 非功能需求

### 7.1 性能

| 指标 | 目标 | 测量方式 |
|------|------|----------|
| 单文档摄取延迟 | < 5s (1MB PDF) | 端到端计时 |
| 语义搜索延迟 | < 500ms (Top-10) | P95 延迟 |
| 并发检索 QPS | ≥ 10 (本地) | 压测 |
| 知识库容量 | ≥ 10,000 条目 | 持续写入测试 |

### 7.2 隐私与安全

| 需求 | 描述 |
|------|------|
| 本地优先 | 所有数据默认存储在用户本地，不上传任何第三方 |
| 加密存储 | 向量和元数据支持可选的 AES-256 加密 |
| 访问控制 | 支持知识库级别的读/写权限控制 |
| 数据隔离 | 不同 Agent 的知识库默认隔离 |
| 审计日志 | 记录知识库的访问和修改操作 |

### 7.3 可扩展性

| 需求 | 描述 |
|------|------|
| 存储后端可替换 | 向量存储支持 ChromaDB → Milvus/Qdrant 切换 |
| Embedding 模型可替换 | 支持本地模型和云端 API 热切换 |
| 解析器可插拔 | 新增文件格式仅需实现 Parser 接口 |
| 水平扩展 | 支持将向量存储和元数据分离部署 |

### 7.4 兼容性

| 需求 | 描述 |
|------|------|
| Python 版本 | 3.10 ~ <3.14（与项目一致） |
| 操作系统 | Linux / macOS / Windows |
| 磁盘占用 | 基础安装 < 500MB（含 Embedding 模型） |

---

## 8. 实现路线图

### Phase 1 — 核心 MVP（预计 2-3 周）

| 任务 | 内容 | 产出 |
|------|------|------|
| P1.1 | 核心数据模型与存储层 | `knowledge_base/store/` |
| P1.2 | 文档摄取管道（TXT/MD/PDF） | `knowledge_base/ingestion/` |
| P1.3 | 智能分块 + 向量化 | `knowledge_base/processing/` |
| P1.4 | 语义搜索 + 关键词搜索 | `knowledge_base/retrieval/` |
| P1.5 | REST API（CRUD + 搜索） | `knowledge_base/api/` |
| P1.6 | Agent Tool 接口 | `knowledge_search` tool |
| P1.7 | 基础单元测试 | 覆盖率 ≥ 80% |

### Phase 2 — 增强功能（预计 2 周）

| 任务 | 内容 | 产出 |
|------|------|------|
| P2.1 | URL 抓取 + HTML 解析 | 扩展 ingestion |
| P2.2 | 集合与标签管理 | 扩展 API + 前端 |
| P2.3 | 混合搜索 + RAG 问答 | 扩展 retrieval |
| P2.4 | Agent 自动检索集成 | 上下文注入 |
| P2.5 | 知识库 Skill | `skills/knowledge-base/` |

### Phase 3 — 高级特性（预计 2-3 周）

| 任务 | 内容 | 产出 |
|------|------|------|
| P3.1 | 批量导入 + 去重 | 扩展 ingestion |
| P3.2 | 对话知识沉淀 | Agent 集成 |
| P3.3 | 导出 + 回收站 | 管理功能 |
| P3.4 | 统计面板 | 可观测性 |
| P3.5 | 知识图谱（可选） | 扩展功能 |

---

## 9. 风险与待决议题

### 9.1 技术风险

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 本地 Embedding 模型质量不足 | 检索精度差 | 支持用户替换模型，提供云端 API 备用方案 |
| 向量存储性能瓶颈 | 大规模知识库检索慢 | 支持切换 Milvus/Qdrant，设计分片策略 |
| 文档解析质量不稳定 | 摄取结果不可用 | 复用成熟的 Office Skills，提供重新解析机制 |
| 与现有 Memory 系统冲突 | 上下文过载 | 明确知识库 vs 记忆的职责边界 |

### 9.2 待决议题

| 议题 | 选项 | 建议 |
|------|------|------|
| 向量存储默认方案 | ChromaDB vs FAISS vs Milvus Lite | ChromaDB（Python 原生，零配置） |
| Embedding 模型默认 | BGE-small-zh (24MB) vs all-MiniLM-L6 (80MB) | BGE-small-zh（体积小，中英文兼顾） |
| 知识库是否支持多用户 | 单用户 vs 多用户 | 单用户（MVP），多用户（P2） |
| 与 Agent Memory 的融合程度 | 深度耦合 vs 松耦合 | 松耦合（独立模块，通过接口集成） |

---

## 附录 A：与现有模块的代码依赖关系

```
knowledge_base/
├── depends on:
│   ├── qwenpaw/agents/tools/file_io.py      (文件读写)
│   ├── qwenpaw/agents/tools/file_search.py  (文件类型判断)
│   ├── qwenpaw/agents/memory/               (存储接口参考)
│   ├── qwenpaw/agents/skill_system/         (Skill 注册)
│   ├── qwenpaw/security/                    (访问控制)
│   └── qwenpaw/config/                      (配置管理)
│
├── consumed by:
│   ├── qwenpaw/agents/context/              (上下文注入)
│   ├── qwenpaw/agents/tools/               (agent_management)
│   └── qwenpaw/app/routers/                (REST 路由注册)
```

## 附录 B：参考项目

| 项目 | 参考价值 |
|------|---------|
| [LangChain / LlamaIndex](https://github.com/run-llama/llama_index) | 文档摄取、索引、检索管道设计 |
| [Dify](https://github.com/langgenius/dify) | 知识库管理 UI 交互模式 |
| [AnythingLLM](https://github.com/Mintplex-Labs/anything-llm) | 本地优先的 RAG 方案 |
| [QwenPaw 现有 Skills](src/qwenpaw/agents/skills/) | 项目内 Skill 结构参考 |