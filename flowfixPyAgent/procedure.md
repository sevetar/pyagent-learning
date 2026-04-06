# FlowFix AI Agent 系统核心流程设计

## 概述

FlowFix 是一个基于 Python + LangChain + FastAPI 实现的 AI Agent 模块，复刻 Java + LangChain4j 的能力。系统包含四大核心功能：**RAG 入库**、**RAG 检索**、**RAG 问答**、**智能分流**和**自动派单**。

---

## 一、RAG 入库流程

### 1.1 流程图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   RabbitMQ      │────▶│ TicketEvent     │────▶│  RagIngester    │────▶│   MySQL         │
│   工单事件       │     │ Consumer        │     │  .ingest_ticket │     │  读取工单数据   │
└─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
                        ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
                        │   pgvector      │◀────│  批量Embedding  │◀────│ split_ticket    │
                        │   写入chunks    │     │  生成向量        │     │  拆分成chunks   │
                        └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### 1.2 详细步骤

| 步骤 | 组件 | 说明 |
|------|------|------|
| 1 | RabbitMQ Consumer | 消费 `ticket.#` 路由键消息，触发入库 |
| 2 | MySQL 读取 | 根据 ticket_id 查询 Ticket 和 TicketProcess 表 |
| 3 | Chunk 拆分 | 将工单拆分为 symptom/cause/solution 三类 chunk |
| 4 | Embedding 生成 | 调用 OpenAI API 批量生成 1536 维向量 |
| 5 | 幂等检查 | 写入前检查 chunk 是否已存在（ticket_id + chunk_type 联合唯一） |
| 6 | pgvector 写入 | 存储向量 + 元数据 + 索引 |

### 1.3 核心代码片段

```python
# 拆分chunk
chunks = self.split_ticket_to_chunks(ticket_data, process_data)
# symptom: 故障现象 / cause: 故障原因 / solution: 维修方案

# 幂等写入
if not self._check_chunk_exists(ticket_id, chunk["chunk_type"]):
    self._write_chunk_with_retry(chunk, ticket_id, embedding, metadata)

# 重试机制
@retry(stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _write_chunk_with_retry(self, chunk, ticket_id, embedding, metadata):
    ...
```

### 1.4 评语

**亮点**：
- **事件驱动架构**：通过 RabbitMQ 解耦工单系统与 RAG 入库，支持异步批量处理
- **语义分块策略**：将工单按 symptom/cause/solution 三元组拆分，检索时可按类型过滤，提高相关性
- **幂等性保障**：唯一约束 `(ticket_id, chunk_type)` 确保重复消费不会重复写入

**难点**：
- **向量维度一致性**：需确保 embedding 模型维度与 pgvector 表定义一致（1536维）
- **批量写入性能**：单个工单可能产生 3 个 chunk，批量处理时需控制并发

**可选方案**：
- 定时轮询数据库变更（CDC）替代 RabbitMQ
- 使用旁路嵌入服务（如 Vertex AI Embeddings）替代 OpenAI

**为什么选择当前方案**：
- RabbitMQ 事件驱动天然适合工单状态变更场景，延迟低
- symptom/cause/solution 三元组拆分是故障诊断场景的最优分块策略

**其他场景优化点**：
- 知识库文档场景可按 `章节 > 段落 > 句子` 多级分块
- 可增加 `last_processed_time` 字段支持增量同步

---

## 二、RAG 检索流程

### 2.1 流程图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   用户查询      │────▶│ generate_       │────▶│  pgvector       │
│   query        │     │ embedding(query)│     │  向量检索        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │ 检索结果        │◀────│  过滤           │
                        │ (top_k=5)       │     │  device_name    │
                        └─────────────────┘     │  chunk_type     │
                                                └─────────────────┘
```

### 2.2 详细步骤

| 步骤 | 组件 | 说明 |
|------|------|------|
| 1 | Query Embedding | 将用户查询文本转为 1536 维向量 |
| 2 | 向量检索 | pgvector `<->` 操作符计算余弦相似度 |
| 3 | 过滤条件 | 可选按 device_name / chunk_type 过滤 |
| 4 | 结果排序 | 按相似度分数降序返回 top_k 条 |

### 2.3 SQL 检索逻辑

```sql
SELECT id, ticket_id, device_name, chunk_type, content, metadata,
       1 - (embedding <=> %s) as similarity  -- 余弦距离转相似度
FROM rag_chunks
WHERE (device_name = %s OR %s IS NULL)
  AND (chunk_type = %s OR %s IS NULL)
ORDER BY embedding <=> %s  -- 最近邻排序
LIMIT %s
```

### 2.4 评语

**亮点**：
- **向量检索**：pgvector 的 `<=>` 操作符支持高效余弦相似度搜索
- **可组合过滤**：device_name + chunk_type 双维度过滤，提高检索精度
- **上下文拼接**：将多条检索结果按固定格式拼接为 LLM 可理解的上下文

**难点**：
- **混合检索**：当前纯向量检索无法满足「设备名=变频器 AND 类型=cause」的精确匹配
- **召回率**：同义词问题（如「报警」vs「告警」）可能导致漏召回

**可选方案**：
- 引入 BM25 稀疏检索与向量检索的混合（RRF 融合）
- 使用 pgvector 的 `ivfflat` 或 `hnsw` 索引加速

**为什么选择当前方案**：
- pgvector 内置支持向量检索，开发成本低
- 过滤条件在应用层组合，灵活可调

**其他场景优化点**：
- 增加「时间窗口」过滤（如只检索近 3 个月案例）
- 引入 rerank 模型（如 Cohere）做二次排序

---

## 三、RAG 问答流程

### 3.1 流程图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   用户问题       │────▶│ RagRetriever    │────▶│ 构建上下文       │
│   query         │     │  .search()      │     │  (history+case) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  流式输出        │◀────│ ChatOpenAI      │
                        │  SSE             │     │  .astream()     │
                        └─────────────────┘     └─────────────────┘
```

### 3.2 详细步骤

| 步骤 | 组件 | 说明 |
|------|------|------|
| 1 | 路由决策 | IntelligentRouter 判断是否走 RAG 流程 |
| 2 | 检索 | RagRetriever.search() 获取 top_k=5 相关案例 |
| 3 | 上下文构建 | build_context() 拼接案例为 prompt |
| 4 | 流式生成 | ChatOpenAI streaming 输出，EventSourceResponse SSE 推送 |
| 5 | 异常处理 | LLM 调用失败时返回友好错误信息 |

### 3.3 系统提示词策略

```python
def get_system_prompt(self) -> str:
    return """你是一个专业的故障诊断助手...
    回答格式：
    - **故障可能原因**：[分析]
    - **建议处理步骤**：[步骤]
    - **参考历史案例**：[案例摘要]
    - **风险提示**：[如有高危因素]"""
```

### 3.4 评语

**亮点**：
- **流式响应**：SSE (Server-Sent Events) 实现打字机效果，用户体验好
- **结构化输出**：强制 LLM 按固定格式回答，便于前端渲染
- **对话历史**：支持传入最近 5 轮对话上下文，实现多轮对话

**难点**：
- **LLM 幻觉**：可能生成看似合理但实际错误的内容
- **Prompt 注入**：用户可能通过问题引导模型偏离系统设定

**可选方案**：
- 接入 Guardrails 做输出校验
- 引入 function calling 限制 LLM 输出格式

**为什么选择当前方案**：
- streaming=True 直接复用 LangChain 的流式能力，改动最小
- 结构化 prompt 比 JSON mode 成本更低

**其他场景优化点**：
- 医疗/金融场景需增加「引用溯源」能力，标注每个答案来自哪个案例
- 可增加「未找到相关案例」的降级回复模板

---

## 四、智能分流流程

### 4.1 流程图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   用户问题       │────▶│ IntelligentRouter│────▶│  LLM 决策       │
│   query         │     │   .decide()     │     │  AUTO/ASSIST/   │
└─────────────────┘     └─────────────────┘     │  MANUAL         │
                                                └─────────────────┘
                                                        │
                              ┌─────────────────┬────────┴────────┐
                              ▼                 ▼                 ▼
                    ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
                    │     AUTO         │ │     ASSIST      │ │     MANUAL      │
                    │  直接RAG回答     │ │ RAG回答+人工确认│ │ 建议走工单流程  │
                    └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 4.2 决策规则

| 决策 | 条件 | 处理方式 |
|------|------|----------|
| AUTO | 通用知识、简单问题、库内有答案 | 直接 RAG 回答 |
| ASSIST | 需要专业判断、可能有解决方案需确认 | RAG 回答 + 人工确认提示 |
| MANUAL | 需现场处理、需审批、复杂问题 | 建议走工单流程 |

### 4.3 核心代码

```python
async def decide(self, query: str, device_name: Optional[str] = None) -> dict:
    response = await self.llm.ainvoke(messages)
    result = json.loads(response.content)

    # 置信度低于0.7时保守返回ASSIST
    if result.get("confidence", 0) < 0.7:
        result["decision"] = "ASSIST"
    return result
```

### 4.4 评语

**亮点**：
- **三级分流**：AUTO/ASSIST/MANUAL 覆盖所有场景，避免过度使用 AI 或工单流程
- **置信度机制**：低于 0.7 时自动降级为 ASSIST，保守策略减少错误决策
- **降级策略**：JSON 解析失败时默认返回 ASSIST，而非直接拒绝服务

**难点**：
- **决策边界模糊**：某些问题处于 ASSIST/MANUAL 边界，难以准确分类
- **Prompt 设计**：决策质量依赖 prompt 的清晰程度

**可选方案**：
- 训练专门的分类模型（如 BERT）做意图分类
- 引入规则引擎（如 Drools）做确定性规则兜底

**为什么选择当前方案**：
- LLM 做分类成本低、可解释性强
- 三级分流足够覆盖工业故障场景

**其他场景优化点**：
- 客服场景可增加第 4 级「转人工」
- 可记录历史决策用于模型微调

---

## 五、自动派单流程

### 5.1 流程图

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   工单信息       │────▶│ AutoDispatcher  │────▶│  获取维修员列表  │
│   ticket_id     │     │    .dispatch() │     │  (技能/负载/效率)│
│   device_type   │     └─────────────────┘     └─────────────────┘
│   fault_type    │                                     │
│   symptom       │                                     ▼
└─────────────────┘     ┌─────────────────┐     ┌─────────────────┐
                        │  派单结果        │◀────│  LLM 决策        │
                        │  (维修员+理由)   │     │  (JSON输出)      │
                        └─────────────────┘     └─────────────────┘
```

### 5.2 决策因素

| 因素 | 说明 | 权重逻辑 |
|------|------|----------|
| 技能匹配 | 维修员 skill_tags 包含 device_type | 必需条件 |
| 当前负载 | current_load 越低越优先 | 负载最低优先 |
| 历史效率 | avg处理时长 越短越优先 | 效率参考 |
| 可用状态 | is_available = 'true' | 必需条件 |

### 5.3 降级策略

```python
# LLM 解析失败时，降级为负载最低策略
if available_repairmen:
    selected = min(available_repairmen, key=lambda r: r["current_load"])
    return DispatchResult(
        repairman_id=selected["id"],
        repairman_name=selected["name"],
        reason="LLM解析失败，降级为负载最低策略",
        confidence=0.3,
    )
```

### 5.4 评语

**亮点**：
- **多维度决策**：综合考虑技能、负载、效率，而非单一指标
- **降级策略**：LLM 不可用时自动降级为「负载最低」规则，避免服务中断
- **可解释输出**：JSON 格式返回派单理由，便于审计和优化

**难点**：
- **负载实时性**：current_load 可能存在延迟，不反映真实忙闲
- **跨技能派单**：紧急情况下可能需要派单给技能不完全匹配的维修员

**可选方案**：
- 引入维修员「最大负载」上限，超限时拒绝新派单
- 使用强化学习根据派单成功率持续优化决策

**为什么选择当前方案**：
- LLM 决策灵活，可处理复杂场景
- 规则降级保障系统可用性

**其他场景优化点**：
- 物流/外卖场景可引入「距离」和「当前订单剩余时间」因素
- 可增加「派单超时」机制，超时未确认自动转派

---

## 六、系统集成流程

### 6.1 完整对话流程

```
用户提问
    │
    ▼
┌───────────────────────────────────────────┐
│  IntelligentRouter.decide()               │
│  → AUTO / ASSIST / MANUAL                 │
└───────────────────────────────────────────┘
    │
    ├── AUTO ──────────────────────────────┐
    │                                       ▼
    │                              RagAnswerGenerator
    │                              流式RAG回答
    │
    ├── ASSIST ────────────────────────────┐
    │                                       ▼
    │                              RAG回答 + 人工确认
    │
    └── MANUAL ────────────────────────────┐
                                        ▼
                              返回工单流程引导
```

### 6.2 事件驱动入库流程

```
工单系统 ──RabbitMQ──▶ TicketEventConsumer ──▶ RagIngester.ingest_ticket()
                                    │
                                    ▼
                            MySQL 读取工单
                                    │
                                    ▼
                            拆分为 symptom/cause/solution
                                    │
                                    ▼
                            OpenAI Embedding
                                    │
                                    ▼
                            pgvector 写入
```

---

## 七、技术选型总结

| 模块 | 技术选型 | 原因 |
|------|----------|------|
| LLM | OpenAI ChatGPT | 通用能力强、成本低 |
| Embedding | OpenAI text-embedding-ada-002 | 与 LLM 同源，兼容性好 |
| 向量数据库 | pgvector (PostgreSQL) | 复用现有数据库，SQL 能力强 |
| 消息队列 | RabbitMQ | 工业级可靠，支持复杂路由 |
| Web 框架 | FastAPI | 异步原生支持，SSE 流式响应 |
| 重试机制 | tenacity | 指数退避，稳态恢复 |

---

*文档生成时间：2026-04-02*
