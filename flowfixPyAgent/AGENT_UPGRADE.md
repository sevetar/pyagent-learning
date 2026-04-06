# AutoDispatcher Agent 升级说明

## 改动概述

将 `AutoDispatcher` 从单次 LLM 调用升级为真正的 **tool-calling agent**，实现多步推理和自主工具调用。

---

## 核心改动

### 1. 新增工具模块 `src/flowfix/agent/tools.py`

定义了 3 个可供 Agent 调用的工具：

#### 🔧 `get_device_fault_history(device_id, limit=5)`
- **功能**：查询设备历史故障记录
- **返回**：设备最近的故障工单，包括故障现象、原因、解决方案
- **使用场景**：了解设备是否有反复出现的问题

#### 🔧 `check_repairman_realtime_load(repairman_id)`
- **功能**：实时查询维修员当前工单负载
- **返回**：维修员的技能标签、当前负载、平均处理时长、进行中工单详情
- **使用场景**：对候选维修员逐一检查负载情况

#### 🔧 `query_similar_cases(symptom, device_name=None, top_k=3)`
- **功能**：从 RAG 知识库检索相似故障案例
- **返回**：相似度最高的历史案例及其处理方案
- **使用场景**：了解类似问题通常由哪类技能的维修员处理

---

### 2. 重构 `src/flowfix/agent/repair_dispatcher.py`

#### 改动前（单次 LLM 调用）
```python
# 直接调用 LLM，返回 JSON 格式的派单决策
response = await self.llm.ainvoke(messages)
result = json.loads(response.content)
```

#### 改动后（Agent 多步推理）
```python
# 使用 LangChain AgentExecutor
self.agent = create_tool_calling_agent(self.llm, ALL_TOOLS, self.prompt)
self.agent_executor = AgentExecutor(
    agent=self.agent,
    tools=ALL_TOOLS,
    verbose=True,  # 打印推理过程
    max_iterations=5,  # 最多 5 步推理
)

# Agent 自主决定调用哪些工具
result = await self.agent_executor.ainvoke({"input": agent_input})
```

#### 关键特性
- **多步推理**：Agent 可以先调用 `get_device_fault_history`，观察结果后再调用 `query_similar_cases`，最后调用 `check_repairman_realtime_load` 确认负载
- **自主决策**：Agent 根据工单信息自主决定是否需要调用工具，以及调用哪些工具
- **降级策略**：如果 Agent 执行失败或输出解析失败，自动降级为"负载最低"规则

---

### 3. 更新 API 接口

#### `src/flowfix/api/schemas.py`
```python
class DispatchRequest(BaseModel):
    ticket_id: int
    device_type: str
    fault_type: str
    symptom: str
    priority: str = "MEDIUM"
    device_id: Optional[int] = None  # 新增：可选的设备ID
```

#### `src/flowfix/api/routes.py`
```python
@router.post("/dispatch")
async def dispatch(request: DispatchRequest) -> DispatchResponse:
    """自动派单接口 - 使用 Agent 自主调用工具进行多步推理"""
    result = await dispatcher.dispatch(
        ticket_id=request.ticket_id,
        device_type=request.device_type,
        fault_type=request.fault_type,
        symptom=request.symptom,
        priority=request.priority,
        device_id=request.device_id,  # 传递给 agent
    )
```

---

## Agent 工作流程示例

### 场景：变频器频繁报警

**输入**：
```json
{
  "ticket_id": 12345,
  "device_type": "变频器",
  "fault_type": "频繁报警",
  "symptom": "设备运行过程中频繁出现过载报警",
  "device_id": 1001
}
```

**Agent 推理过程**（verbose 输出）：
```
1. 调用 get_device_fault_history(device_id=1001)
   → 发现该设备过去 3 个月内有 5 次类似报警记录

2. 调用 query_similar_cases(symptom="频繁出现过载报警", device_name="变频器")
   → 检索到 3 个相似案例，发现通常由"电气维修"技能的维修员处理

3. 调用 check_repairman_realtime_load(repairman_id=101)
   → 维修员张三（技能：电气维修），当前负载 2 个工单

4. 调用 check_repairman_realtime_load(repairman_id=102)
   → 维修员李四（技能：电气维修），当前负载 5 个工单

5. 最终决策：选择维修员张三（ID: 101）
```

**输出**：
```json
{
  "repairman_id": 101,
  "repairman_name": "张三",
  "reason": "该设备历史上有多次类似报警记录，相似案例显示需要电气维修技能。张三具备该技能且当前负载较低（2个工单），处理效率高。",
  "confidence": 0.85
}
```

---

## 与之前的区别

| 维度 | 改动前 | 改动后 |
|------|--------|--------|
| **决策方式** | 单次 LLM 调用，基于静态维修员列表 | Agent 多步推理，主动调用工具收集信息 |
| **信息来源** | 仅使用传入的维修员列表 | 查询设备历史、检索相似案例、实时查询负载 |
| **推理过程** | 黑盒，无法观察 | 可通过 verbose 输出观察每一步工具调用 |
| **是否为 Agent** | ❌ 不是，只是 LLM + 结构化输出 | ✅ 是，符合 ReAct 模式的 tool-calling agent |

---

## 如何测试

### 1. 运行测试脚本
```bash
cd flowfixPyAgent
uv run python test_agent.py
```

### 2. 观察要点
- Agent 是否自主调用了工具（观察 verbose 输出）
- Agent 是否进行了多步推理（先查历史 → 再查案例 → 最后查负载）
- 最终派单决策是否综合了工具返回的信息

### 3. API 测试
```bash
curl -X POST http://localhost:8000/api/v1/dispatch \
  -H "Content-Type: application/json" \
  -d '{
    "ticket_id": 12345,
    "device_type": "变频器",
    "fault_type": "频繁报警",
    "symptom": "设备运行过程中频繁出现过载报警",
    "priority": "HIGH",
    "device_id": 1001
  }'
```

---

## 面试话术建议

**面试官**：你的项目里有 AI Agent 吗？

**你**：有的，我实现了一个基于 LangChain 的 AutoDispatcher Agent，用于工单自动派单。

**面试官**：能说说它是怎么工作的吗？

**你**：
1. **工具定义**：我定义了 3 个工具 —— 查询设备历史故障、查询维修员实时负载、检索相似案例
2. **Agent 推理**：使用 LangChain 的 `create_tool_calling_agent` 和 `AgentExecutor`，Agent 会根据工单信息自主决定调用哪些工具
3. **多步决策**：比如遇到设备反复故障的工单，Agent 会先查设备历史，发现有多次类似问题后，再检索相似案例了解处理经验，最后对比候选维修员的实时负载，选择最合适的人
4. **降级策略**：如果 Agent 执行失败，会自动降级为"负载最低"规则，保障系统可用性

**面试官**：这和直接调用 LLM 有什么区别？

**你**：
- 直接调用 LLM 是单次决策，只能基于传入的静态信息
- Agent 是多步推理，可以主动调用工具收集信息，观察结果后再决定下一步
- 这符合 ReAct（Reasoning + Acting）模式，是真正的 tool-calling agent

---

## 文件清单

```
flowfixPyAgent/
├── src/flowfix/agent/
│   ├── tools.py                    # 新增：工具定义
│   ├── repair_dispatcher.py        # 重构：Agent 实现
│   └── __init__.py                 # 无需改动
├── src/flowfix/api/
│   ├── schemas.py                  # 更新：DispatchRequest 增加 device_id
│   └── routes.py                   # 更新：dispatch 接口传递 device_id
└── test_agent.py                   # 新增：测试脚本
```

---

## 总结

通过这次改动，`AutoDispatcher` 从一个"LLM 增强的规则引擎"升级为真正的 **tool-calling agent**，具备了：
- ✅ 自主工具调用能力
- ✅ 多步推理能力
- ✅ 可观察的推理过程
- ✅ 降级保障机制

这样在面试时就可以自信地说："我实现了一个基于 LangChain 的 AI Agent，它能自主调用工具进行多步推理，完成复杂的派单决策任务。"
