# FlowFix 协作调度平台中｜AI Agent + RAG 功能 Spec Coding 提示词

> 目标：基于我简历中的学习项目，使用 **Python + LangChain+fastapi** 复刻原来 Java + LangChain4j 实现的 AI Agent 能力。请以“可落地、可扩展、可测试”的工程标准输出代码与设计，不要只给概念解释。
不过我其实我不打算把这个py的ai agent融入之前的java项目，也就是说，mysql和其他的组件都是隔离的，
只要测试数据能跑通就行
环境用uv
## 1. 项目背景

FlowFix 是一个基于 Spring Cloud 的企业协作调度平台，核心业务包括设备报修、审批流转、抢单派工、权限控制和搜索。现在需要在 Python 侧补齐一个 AI Agent 模块，复刻并增强以下能力：

* 基于 **RAG** 的故障知识检索与回答
* 基于 **Agent 决策** 的工单智能分流
* 基于 **Agent 调度** 的维修人员自动派单
* 采用 **流式响应** 提升交互体验

系统的数据来源包括：

* **MySQL**：工单主表、工单处理记录表、状态流转日志
* **RabbitMQ**：工单创建/完成/更新等事件
* **PostgreSQL + pgvector**：RAG 向量知识库

---



## 2. 这次要实现的功能范围

请实现一个完整的 AI Agent 子系统，拆成三个闭环能力：

### 2.1 RAG 知识入库与问答

当工单状态变化或工单完成时，消费 RabbitMQ 消息，从 MySQL 中读取工单主表与处理记录表，拆分为多个语义 chunk，生成 embedding，写入 PostgreSQL 的 pgvector 表中；查询时通过相似度检索召回历史故障案例，并结合 LLM 生成回答。

### 2.2 智能分流

Agent 根据当前用户问题复杂度，将请求分为：

* `AUTO`：AI 可直接回复
* `ASSIST`：AI 给出建议，但需要人工确认
* `MANUAL`：进入完整工单流程

### 2.3 自动派单

当工单进入需要人工处理的分支后，Agent 根据以下因素选择维修人员：

* 设备类型 / 故障类型
* 维修员技能标签
* 当前负载
* 历史处理效率

---

## 3. 数据模型设计要求

### 3.1 MySQL 侧建议表结构

请以“工单主表 + 处理记录表 + 流转日志表”的方式建模，不要把所有字段塞到一张表里。

#### ticket（工单主表）
CREATE TABLE ticket (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '工单ID',

    user_id BIGINT NOT NULL COMMENT '用户ID',
    device_id BIGINT COMMENT '设备ID',
    device_name VARCHAR(100) COMMENT '设备名称',

    title VARCHAR(255) COMMENT '工单标题',
    symptom TEXT COMMENT '故障现象（用户描述）',

    status VARCHAR(50) NOT NULL COMMENT '状态（CREATED / APPROVED / ASSIGNED / PROCESSING / DONE / CLOSED）',

    priority VARCHAR(20) DEFAULT 'MEDIUM' COMMENT '优先级（LOW / MEDIUM / HIGH）',

    assigned_to BIGINT COMMENT '当前处理人（维修员ID）',

    version INT DEFAULT 0 COMMENT '乐观锁版本号（@Version）',

    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    INDEX idx_user_id (user_id),
    INDEX idx_status (status),
    INDEX idx_device_id (device_id)
);

存储工单基础信息、当前状态、用户故障现象、乐观锁版本等。

#### ticket_process（工单处理记录表）
CREATE TABLE ticket_process (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '处理记录ID',

    ticket_id BIGINT NOT NULL COMMENT '工单ID',

    operator_id BIGINT NOT NULL COMMENT '操作人ID',
    operator_role VARCHAR(50) COMMENT '角色（USER / ADMIN / REPAIRMAN）',

    action VARCHAR(50) NOT NULL COMMENT '操作类型（CREATE / APPROVE / ASSIGN / REPAIR / CLOSE）',

    cause TEXT COMMENT '故障原因（维修员填写）',
    solution TEXT COMMENT '维修方案',

    result VARCHAR(50) COMMENT '处理结果（SUCCESS / FAIL）',

    remark TEXT COMMENT '备注信息',

    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_ticket_id (ticket_id),
    INDEX idx_operator_id (operator_id)
);

存储维修员/审批员的处理过程、故障原因、维修方案、派单结果等。

#### ticket_log（工单流转日志表）
CREATE TABLE ticket_log (
    id BIGINT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',

    ticket_id BIGINT NOT NULL COMMENT '工单ID',

    from_status VARCHAR(50) COMMENT '变更前状态',
    to_status VARCHAR(50) NOT NULL COMMENT '变更后状态',

    operator_id BIGINT COMMENT '操作人ID',

    event_type VARCHAR(50) COMMENT '事件类型（APPROVE / ASSIGN / FINISH / REJECT）',

    remark TEXT COMMENT '备注',

    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,

    INDEX idx_ticket_id (ticket_id)
);

存储状态从什么变到什么、谁操作的、何时操作的。

### 3.2 PostgreSQL 向量表设计

向量知识表建议如下：

```sql
CREATE TABLE fault_knowledge (
    id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT,
    device_name TEXT,
    chunk_type VARCHAR(20),
    content TEXT,
    embedding VECTOR(1536),
    metadata JSONB,
    create_time TIMESTAMP
);
```

请注意：

* `content` 必须保留原始可读文本
* `embedding` 用于语义检索
* `metadata` 用于过滤与追踪（如 user_id、device_id、priority、status、source 等）
* `chunk_type` 至少支持：`symptom`、`cause`、`solution`

### 3.3 Chunk 拆分规则

每个工单至少拆成 3 个 chunk：

1. `symptom`：用户描述的故障现象
2. `cause`：维修员给出的故障原因
3. `solution`：维修方案 / 处理建议

每个 chunk 单独 embedding，单独写入一条向量记录。

---

## 4. RAG 写入流程要求

请实现以下数据流：

1. 用户提交工单，MySQL 写入成功
2. 业务服务发送 RabbitMQ 事件
3. RAG 服务消费消息
4. RAG 服务根据 `ticket_id` 查询 MySQL 的工单主表与处理记录表
5. 按规则拆分 chunk
6. 生成 embedding
7. 写入 PostgreSQL pgvector

### 4.1 写入要求

* 需要保证幂等，避免 RabbitMQ 重复消费导致重复写入
* 需要有失败重试机制
* 需要记录入库日志，便于排查问题
* 支持后续历史数据补录

### 4.2 检索要求

* 查询时支持按 `device_name`、`chunk_type`、`metadata` 进行过滤
* 优先做向量召回，再结合 metadata 精筛
* 最终将召回结果拼接为上下文，交给 LLM 生成回答

---

## 5. Agent 决策系统要求

请把 AI Agent 设计成一个“工单决策与执行中枢”，不是简单聊天机器人。

### 5.1 智能分流

输入用户问题后，Agent 先判断：

* 是否可以直接由知识库回答
* 是否需要人工介入
* 是否必须走完整工单流程

输出必须是结构化结果，例如：

* `AUTO`
* `ASSIST`
* `MANUAL`

### 5.2 自动派单

当工单需要人工处理时，Agent 根据：

* 工单类型
* 设备类型
* 维修员技能标签
* 当前负载
* 历史平均处理时长

选择最合适的维修人员，并返回结构化派单结果。

### 5.3 RAG 处理

当 Agent 判定可通过知识增强回答时：

* 先做检索
* 再做答案生成
* 输出维修建议、参考历史工单、风险提示
* 支持流式输出，前端可以实时接收生成内容

---

## 6. 工程实现要求

请优先采用以下工程原则：

* Python 3.11+
* LangChain 作为 Agent / RAG 编排框架
* PostgreSQL + pgvector 作为向量库
* MySQL 作为业务源数据
* RabbitMQ 作为异步事件总线
* 代码结构要模块化，便于扩展和测试
* 所有关键逻辑必须有清晰边界，不要把业务逻辑写成一坨
* 对外暴露的接口要考虑流式响应
* 需要考虑失败重试、幂等、日志、异常兜底

---

## 7. 输出内容要求

请最终输出：

1. 推荐的目录结构
2. 核心表设计建议
3. 关键类 / 模块设计
4. RAG 入库与检索流程
5. Agent 决策流程
6. 自动派单流程
7. 可运行的核心代码骨架
8. 关键接口示例
9. 用于面试表达的简洁总结

---

## 8. 验收标准

请确保方案满足以下条件：

* 能从 MySQL 工单数据中构建向量知识库
* 能基于问题内容进行检索增强回答
* 能根据规则或模型做智能分流
* 能对维修人员做自动派单
* 能支持流式输出
* 能保证消息消费幂等与最终一致性
* 能解释清楚每个模块的职责边界

---

## 9. 额外约束

* 不要只给“概念说明”，请给具体实现思路
* 不要把所有内容写死在一个文件里
* 不要忽略异常处理和降级逻辑
* 不要省略表设计与消息流转设计
* 如果有更好的工程方案，请优先给出更优方案并说明原因

---

## 10. 你可以直接开始做的方向

优先从以下顺序实现：

1. MySQL 表设计
2. RabbitMQ 消息格式定义
3. RAG 入库消费任务
4. pgvector 检索与问答
5. Agent 分流与派单决策
6. 流式输出接口
7. 幂等、重试、补偿任务

> 请基于以上要求，输出一个可落地的 Python 方案。
