# 多Agent系统功能文档

本文档介绍基于docs2/集成的多Agent系统功能。

## 功能概览

### 1. 长期记忆 (Long-term Memory)
- **文件**: `agents/memory_agent.py`
- **存储方案**: InMemoryStore
- **功能**: 跨会话记忆用户信息，提供个性化回复
- **特点**:
  - 短期记忆: MemorySaver (会话内记忆)
  - 长期记忆: InMemoryStore (跨会话记忆)
  - 自动提取关键信息并存储
  - 基于用户ID隔离记忆

### 2. RAG检索增强生成 (Retrieval-Augmented Generation)
- **文件**: `agents/rag_agent.py`
- **向量存储**: InMemoryVectorStore
- **架构**: Agentic RAG模式
- **流程**:
  1. 检索相关文档
  2. 评分判断相关性
  3. 如果不相关则重新检索
  4. 基于相关文档生成回答

### 3. Router路由模式
- **文件**: `agents/multi_agent_system.py` - RouterAgent类
- **功能**: 根据查询类型自动路由到专家Agent
- **支持的专家**:
  - 天气专家: 处理天气查询
  - 通用专家: 处理一般性查询

### 4. Subagents监督模式
- **文件**: `agents/multi_agent_system.py` - SupervisorAgent类
- **功能**: 监督Agent调用子Agent作为工具
- **子Agent**:
  - 天气子Agent: 使用get_weather工具
  - 搜索子Agent: 使用search_info工具
- **流程**:
  1. 监督Agent分析查询
  2. 决定调用哪个子Agent
  3. 子Agent执行任务并返回结果
  4. 监督Agent生成最终回答

### 5. Handoffs交接模式
- **文件**: `agents/multi_agent_system.py` - HandoffAgent类
- **功能**: Agent间状态驱动的动态切换
- **Agent角色**:
  - 分诊Agent: 初步判断用户需求
  - 销售Agent: 处理销售咨询
  - 技术支持Agent: 处理技术问题
- **特点**: Agent可以相互转接，实现复杂的对话流程

## 使用示例

### 运行演示
```bash
uv run demo_multi_agent.py
```

### 代码示例

#### 1. 长期记忆Agent
```python
from agents.memory_agent import MemoryAgent

agent = MemoryAgent()

# 第一次对话
response = agent.chat("我叫张三，我喜欢Python", user_id="user123")

# 第二次对话 - Agent会记住之前的信息
response = agent.chat("你还记得我的名字吗？", user_id="user123")
```

#### 2. RAG Agent
```python
from agents.rag_agent import RAGAgent

agent = RAGAgent()

# 添加知识库
documents = [
    "LangChain是一个用于开发语言模型应用的框架。",
    "LangGraph用于构建有状态的多Actor应用程序。"
]
agent.add_documents(documents)

# 查询
response = agent.chat("LangGraph是什么？")
```

#### 3. Router Agent
```python
from agents.multi_agent_system import RouterAgent

agent = RouterAgent()

# 自动路由到天气专家
response = agent.chat("北京今天天气怎么样？")

# 自动路由到通用专家
response = agent.chat("什么是人工智能？")
```

#### 4. Supervisor Agent
```python
from agents.multi_agent_system import SupervisorAgent

agent = SupervisorAgent()

# 监督Agent会调用天气子Agent
response = agent.chat("上海的天气如何？")

# 监督Agent会调用搜索子Agent
response = agent.chat("搜索LangChain的最新信息")
```

#### 5. Handoff Agent
```python
from agents.multi_agent_system import HandoffAgent

agent = HandoffAgent()

# 路由到销售Agent
response = agent.chat("我想购买你们的产品")

# 路由到技术支持Agent
response = agent.chat("我的系统出现了错误")
```

## 技术架构

### 核心依赖
- LangChain: 语言模型框架
- LangGraph: 状态图构建
- InMemoryStore: 长期记忆存储
- InMemoryVectorStore: 向量存储
- MemorySaver: 短期记忆检查点

### 状态管理
所有Agent都使用LangGraph的状态图进行流程控制：
- MessagesState: 消息状态管理
- 条件边: 动态路由决策
- 检查点: 会话持久化

### 记忆层次
1. **短期记忆** (MemorySaver): 单次会话内的上下文
2. **长期记忆** (InMemoryStore): 跨会话的用户信息
3. **知识库** (VectorStore): 检索增强的外部知识

## 扩展建议

### 1. 持久化存储
当前使用InMemoryStore，生产环境可替换为：
- PostgreSQL + pgvector
- Redis
- Chroma
- Pinecone

### 2. 更多Agent类型
可以添加：
- 代码生成Agent
- 数据分析Agent
- 文档总结Agent
- 翻译Agent

### 3. 人机协同
可以集成Human-in-the-loop功能：
- 关键决策需要人工确认
- 使用interrupt()暂停执行
- 等待用户输入后继续

### 4. 监控和日志
添加：
- Agent执行追踪
- 性能监控
- 错误日志
- 用户行为分析

## 参考文档
- docs2/long-term memory.txt
- docs2/retrieval.txt
- docs2/router.txt
- docs2/subagent.txt
- docs2/Handoffs.txt
