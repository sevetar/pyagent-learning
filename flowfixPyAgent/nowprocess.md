# FlowFix AI Agent 项目进度

> 最后更新: 2026-03-31

## 项目概述

基于 Python + LangChain + FastAPI 实现的 AI Agent 模块，支持 RAG 知识问答、智能分流、自动派单、流式响应。

---
  flowfixPyAgent/
  ├── src/flowfix/
  │   ├── config.py           # 配置管理
  │   ├── main.py            # CLI入口
  │   ├── api/                # FastAPI接口
  │   │   ├── routes.py       # 路由定义
  │   │   └── schemas.py      # Pydantic模型
  │   ├── agent/              # Agent决策模块
  │   │   ├── dispatcher.py  # 智能分流
  │   │   └── repair_dispatcher.py  # 自动派单
  │   ├── core/              # 核心组件
  │   │   └── consumer.py    # RabbitMQ消费者
  │   ├── db/                # 数据库模块
  │   │   ├── models.py      # SQLAlchemy模型
  │   │   ├── database.py    # MySQL连接
  │   │   ├── vector_db.py   # pgvector操作
  │   │   └── schema.sql     # 数据库初始化SQL
  │   ├── rag/               # RAG模块
  │   │   ├── embedding.py   # Embedding生成
  │   │   ├── ingestion.py   # RAG数据入库
  │   │   ├── retrieval.py   # 向量检索
  │   │   └── answer.py      # 答案生成
  │   └── utils/             # 工具模块
  ├── tests/                 # 测试
  ├── pyproject.toml         # uv项目配置
  ├── README.md             # 项目文档
  ├── nowprocess.md         # 进度追踪
  └── need.md                # 需求文档

  已实现的核心功能

  1. RAG 知识入库 - 从 MySQL 读取工单，拆分为 symptom/cause/solution chunk，写入 pgvector
  2. RAG 检索问答 - 向量相似度检索 + LLM 流式生成回答
  3. 智能分流 - AUTO/ASSIST/MANUAL 三级分流
  4. 自动派单 - 基于技能/负载/效率的 LLM 决策
  5. RabbitMQ 消费者 - 事件驱动触发 RAG 入库
  6. FastAPI 流式接口 - SSE 流式响应
  7. 幂等性保障 - 唯一约束 + 重试机制

## 已完成功能

### 1. 项目结构搭建 ✅
- 使用 uv 作为包管理器
- 完整的模块化目录结构
- 配置管理 (pydantic-settings)
- 结构化日志 (structlog)

### 2. 数据库模型设计 ✅

**MySQL 表 (src/flowfix/db/models.py)**:
- `ticket` - 工单主表
- `ticket_process` - 工单处理记录表
- `ticket_log` - 工单流转日志表
- `repairman` - 维修员表

**PostgreSQL/pgvector (src/flowfix/db/vector_db.py)**:
- `fault_knowledge` - 向量知识库表
- 支持 VECTOR(1536) embedding
- JSONB metadata 存储

### 3. RAG 入库模块 ✅

**模块**: `src/flowfix/rag/ingestion.py`

**功能**:
- 从 MySQL 读取工单主表和处理记录
- 拆分为 3 个 chunk: symptom / cause / solution
- 批量生成 embedding
- 写入 pgvector (幂等性保障)
- 失败重试机制 (tenacity)

**幂等性**: 通过 `ticket_id + chunk_type` 唯一约束实现

### 4. RAG 检索与问答模块 ✅

**检索 (src/flowfix/rag/retrieval.py)**:
- 向量相似度检索
- 支持 device_name、chunk_type 过滤
- 上下文拼接

**答案生成 (src/flowfix/rag/answer.py)**:
- 基于历史案例的问答
- 流式输出 (AsyncGenerator)
- System prompt 工程化设计

### 5. 智能分流 Agent ✅

**模块**: `src/flowfix/agent/dispatcher.py`

**功能**:
- 三级分流: AUTO / ASSIST / MANUAL
- LLM 决策 + JSON 输出解析
- 置信度评估
- 降级策略

### 6. 自动派单 Agent ✅

**模块**: `src/flowfix/agent/repair_dispatcher.py`

**功能**:
- 综合考虑: 技能匹配、当前负载、历史效率
- LLM 决策选择最优维修员
- 降级策略: 负载最低优先

### 7. RabbitMQ 消费者 ✅

**模块**: `src/flowfix/core/consumer.py`

**功能**:
- Topic 交换机订阅 (ticket.#)
- 消息解析与路由
- 触发 RAG 入库
- 失败重试 (requeue)
- QoS 限流

### 8. FastAPI 流式接口 ✅

**模块**: `src/flowfix/api/routes.py`

**接口**:
- `POST /api/v1/chat/stream` - 流式聊天
- `POST /api/v1/chat` - 非流式聊天
- `POST /api/v1/route` - 分流决策
- `POST /api/v1/dispatch` - 派单决策
- `POST /api/v1/rag/ingest` - RAG 入库
- `GET /api/v1/health` - 健康检查

### 9. CLI 工具 ✅

**模块**: `src/flowfix/main.py`

**命令**:
- `python -m flowfix.main api` - 启动 API
- `python -m flowfix.main consumer` - 启动消费者
- `python -m flowfix.main init-db` - 初始化数据库
- `python -m flowfix.main ingest-ticket --ticket-id X` - 手动入库

---

## 正在实现 / 待完善

### 1. 对话历史管理 🔄
- 当前 conversation_history 仅支持简单存储
- 需要接入持久化存储 (Redis)
- 需要 session 管理

### 2. 维修员技能标签匹配 🔄
- 当前 skill_tags 为 JSON 存储
- 简单的字符串匹配
- 可优化为向量匹配

### 3. 批量历史数据补录 🔄
- 支持从指定时间范围批量导入
- 需要分页和进度展示
- 并发控制

### 4. 测试覆盖 🔄
- 已有基础测试骨架
- 需要补充集成测试
- Mock LLM 调用

---

## 实现到哪一步

| 模块 | 状态 | 说明 |
|------|------|------|
| 项目结构 | ✅ 完成 | uv + 模块化 |
| 数据库模型 | ✅ 完成 | MySQL + pgvector |
| RAG 入库 | ✅ 完成 | 幂等 + 重试 |
| RAG 检索 | ✅ 完成 | 向量搜索 |
| RAG 问答 | ✅ 完成 | 流式输出 |
| 智能分流 | ✅ 完成 | 三级分流 |
| 自动派单 | ✅ 完成 | LLM 决策 |
| RabbitMQ 消费者 | ✅ 完成 | 事件驱动 |
| FastAPI 接口 | ✅ 完成 | 流式响应 |
| CLI 工具 | ✅ 完成 | 运维支持 |

**核心功能已完成**，可以跑通基本流程。待完善的主要是辅助功能如对话历史持久化、批量数据补录等。

---

## 如何运行

```bash
# 1. 安装依赖
uv sync

# 2. 复制并编辑配置
cp .env.example .env

# 3. 初始化数据库
# MySQL: 执行 db/schema.sql
# PostgreSQL: 执行 db/schema.sql (需先安装 pgvector)

# 4. 启动 API
uv run python -m flowfix.main api

# 5. 启动消费者 (另一个终端)
uv run python -m flowfix.main consumer
```

---

## 验收标准对照

| 标准 | 状态 |
|------|------|
| 能从 MySQL 工单数据中构建向量知识库 | ✅ |
| 能基于问题内容进行检索增强回答 | ✅ |
| 能根据规则或模型做智能分流 | ✅ |
| 能对维修人员做自动派单 | ✅ |
| 能支持流式输出 | ✅ |
| 能保证消息消费幂等与最终一致性 | ✅ |
| 能解释清楚每个模块的职责边界 | ✅ |
