# FlowFix AI Agent + RAG 系统

基于 Python + LangChain + FastAPI 实现的 AI Agent 模块，复刻 Java + LangChain4j 的能力。

## 项目结构

```
flowfixPyAgent/
├── src/flowfix/
│   ├── __init__.py
│   ├── config.py          # 配置管理
│   ├── main.py             # CLI入口
│   ├── api/                # FastAPI接口
│   │   ├── __init__.py
│   │   ├── routes.py       # 路由定义
│   │   └── schemas.py       # Pydantic模型
│   ├── agent/              # Agent决策模块
│   │   ├── __init__.py
│   │   ├── dispatcher.py   # 智能分流
│   │   └── repair_dispatcher.py  # 自动派单
│   ├── core/               # 核心组件
│   │   ├── __init__.py
│   │   └── consumer.py     # RabbitMQ消费者
│   ├── db/                 # 数据库模块
│   │   ├── __init__.py
│   │   ├── models.py       # SQLAlchemy模型
│   │   ├── database.py     # MySQL连接
│   │   ├── vector_db.py    # PostgreSQL/pgvector
│   │   └── schema.sql      # 数据库初始化SQL
│   ├── rag/                # RAG模块
│   │   ├── __init__.py
│   │   ├── embedding.py    # Embedding生成
│   │   ├── ingestion.py    # RAG数据入库
│   │   ├── retrieval.py    # 向量检索
│   │   └── answer.py       # 答案生成
│   └── utils/              # 工具模块
│       └── __init__.py
├── tests/                  # 测试
├── data/                   # 数据目录
├── pyproject.toml
├── .env.example
└── README.md
```

## 环境要求

- Python 3.11+
- uv (包管理)
- MySQL 8.0+
- PostgreSQL 15+ (需安装 pgvector 扩展)
- RabbitMQ 3.x
- OpenAI API Key

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置环境

```bash
cp .env.example .env
# 编辑 .env 填入实际配置
```

### 3. 初始化数据库

```bash
# MySQL 执行 db/schema.sql
# PostgreSQL 执行 db/schema.sql

# 或使用 CLI 初始化
uv run python -m flowfix.main init-db
```

### 4. 启动服务

```bash
# 启动 API 服务
uv run python -m flowfix.main api

# 启动 RabbitMQ 消费者
uv run python -m flowfix.main consumer
```

## API 接口

### 聊天接口 (流式)

```
POST /api/v1/chat/stream
{
    "query": "设备报警E001怎么处理",
    "device_name": "变频器A",
    "user_id": 1
}
```

### 分流决策

```
POST /api/v1/route
{
    "query": "设备报警E001怎么处理",
    "device_name": "变频器A"
}
```

### 自动派单

```
POST /api/v1/dispatch
{
    "ticket_id": 1001,
    "device_type": "变频器",
    "fault_type": "报警故障",
    "symptom": "显示E001报警代码",
    "priority": "HIGH"
}
```

### RAG入库

```
POST /api/v1/rag/ingest
{
    "ticket_id": 1001
}
```

## 核心功能

### 1. RAG 知识入库与问答

- 消费 RabbitMQ 消息触发入库
- 从 MySQL 读取工单和处理记录
- 拆分为 symptom/cause/solution 三个 chunk
- 生成 embedding 存入 pgvector
- 支持按设备名、chunk类型过滤检索
- 流式输出回答

### 2. 智能分流

- AUTO: AI 直接回答
- ASSIST: AI 建议 + 人工确认
- MANUAL: 进入完整工单流程

### 3. 自动派单

- 根据设备类型、故障类型匹配维修员
- 综合考虑技能标签、当前负载、历史效率
- LLM 决策 + 降级策略

### 4. 工程特性

- 幂等性保障 (唯一约束)
- 失败重试 (tenacity)
- 流式响应 (SSE)
- 结构化日志 (structlog)
- 完整错误处理
