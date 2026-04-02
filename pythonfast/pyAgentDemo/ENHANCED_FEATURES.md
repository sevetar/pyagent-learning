# LangChain 增强功能文档

本项目展示了如何在 LangChain + GPT-4o-mini 项目中实现以下高级功能：

## 功能列表

### 1. Short-term Memory (短期记忆) ✅

使用 `MemorySaver` 实现对话历史记忆，支持多轮对话。

**实现方式：**
```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
agent = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=memory  # 启用记忆
)
```

**使用示例：**
```python
agent = EnhancedWeatherAgent()

# 第一轮对话
agent.chat("我叫张三，我在北京")

# 第二轮对话 - 代理会记住之前的信息
agent.chat("我叫什么名字？")  # 回答：张三
agent.chat("我在哪里？")      # 回答：北京

# 清空记忆
agent.clear_history()
```

**特点：**
- 基于 `thread_id` 隔离不同会话
- 支持获取记忆摘要
- 可以随时清空历史

---

### 2. Streaming (流式传输) ✅

实时输出 AI 响应，提升用户体验。

**实现方式：**
```python
async def chat_stream(self, message: str):
    async for event in self.agent.astream_events(
        {"messages": [("user", message)]},
        config=config,
        version="v2"
    ):
        if event.get("event") == "on_chat_model_stream":
            content = event.get("data", {}).get("chunk", {})
            if hasattr(content, "content"):
                yield content.content
```

**使用示例：**
```python
agent = EnhancedWeatherAgent()

async for chunk in agent.chat_stream("介绍一下人工智能"):
    print(chunk, end="", flush=True)
```

**特点：**
- 实时输出，无需等待完整响应
- 使用 `astream_events` API
- 支持异步操作

---

### 3. Structured Output (结构化输出) ✅

将 AI 响应转换为结构化的 Pydantic 模型。

**GPT-4o-mini 支持原生的结构化输出功能！**

**实现方式：**
```python
from pydantic import BaseModel, Field

class WeatherResponse(BaseModel):
    answer: str = Field(description="回答")
    city: str = Field(description="城市")
    weather_info: str = Field(description="天气信息")

# 使用原生 structured output
structured_llm = llm.with_structured_output(WeatherResponse)
response = structured_llm.invoke(prompt)
```

**使用示例：**
```python
agent = EnhancedWeatherAgent()

response = agent.chat_structured(
    "北京今天天气怎么样？",
    response_model=WeatherResponse
)

print(response.city)          # 北京
print(response.weather_info)  # 晴天，15-25°C
```

**特点：**
- 使用 Pydantic 模型定义响应格式
- 原生支持，无需提示工程
- 自动解析和验证

---

### 4. Middleware (中间件) ✅

在请求前后执行自定义逻辑。

**预构建中间件：**

1. **LoggingMiddleware** - 日志记录
```python
class LoggingMiddleware:
    def before_invoke(self, context):
        print(f"收到请求: {context.user_message}")

    def after_invoke(self, context, response):
        print(f"响应长度: {len(response)}")
```

2. **RateLimitMiddleware** - 速率限制
```python
class RateLimitMiddleware:
    def __init__(self, max_requests: int = 10):
        self.max_requests = max_requests
        self.request_count = 0

    def before_invoke(self, context):
        self.request_count += 1
        if self.request_count > self.max_requests:
            raise Exception("超过速率限制")
```

**自定义中间件：**
```python
class WordCountMiddleware:
    def __init__(self):
        self.total_words = 0

    def before_invoke(self, context):
        word_count = len(context.user_message.split())
        print(f"用户消息字数: {word_count}")

    def after_invoke(self, context, response):
        word_count = len(response.split())
        self.total_words += word_count
        print(f"助手回复字数: {word_count}")

# 使用
agent = EnhancedWeatherAgent(enable_middleware=False)
agent.add_middleware(WordCountMiddleware())
```

**特点：**
- 支持前置和后置钩子
- 可以添加多个中间件
- 按顺序执行

---

## 项目结构

```
pyAgentDemo/
├── config/
│   ├── __init__.py
│   └── settings.py           # 配置管理
├── tools/
│   ├── __init__.py
│   └── weather_tools.py      # 工具定义
├── agents/
│   ├── __init__.py
│   ├── weather_agent.py      # 基础代理
│   └── enhanced_agent.py     # 增强代理（包含所有高级功能）
├── main.py                   # 基础演示
├── demo_enhanced.py          # 增强功能演示
├── .env                      # 环境变量
└── pyproject.toml
```

---

## 快速开始

### 1. 安装依赖
```bash
uv sync
```

### 2. 配置环境变量
编辑 `.env` 文件：
```env
DEEPSEEK_API_KEY=your_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
```

### 3. 运行演示

**基础演示：**
```bash
uv run main.py
```

**增强功能演示：**
```bash
uv run demo_enhanced.py
```

---

## 使用示例

### 完整示例

```python
from agents import EnhancedWeatherAgent, WeatherResponse

# 创建代理（启用中间件）
agent = EnhancedWeatherAgent(enable_middleware=True)

# 1. 标准对话
response = agent.chat("北京今天天气怎么样？")
print(response)

# 2. 流式对话
import asyncio

async def stream_demo():
    async for chunk in agent.chat_stream("介绍一下 AI"):
        print(chunk, end="", flush=True)

asyncio.run(stream_demo())

# 3. 结构化输出
response = agent.chat_structured(
    "上海今天天气怎么样？",
    response_model=WeatherResponse
)
print(f"城市: {response.city}")
print(f"天气: {response.weather_info}")

# 4. 多轮对话（测试记忆）
agent.chat("我叫李四")
agent.chat("我叫什么名字？")  # 会记住

# 5. 添加自定义中间件
class CustomMiddleware:
    def before_invoke(self, context):
        print("自定义前置逻辑")

    def after_invoke(self, context, response):
        print("自定义后置逻辑")

agent.add_middleware(CustomMiddleware())

# 6. 获取记忆摘要
summary = agent.get_memory_summary()
print(f"对话轮数: {summary['message_count']}")

# 7. 清空记忆
agent.clear_history()
```

---

## 技术细节

### Memory 实现
- 使用 `MemorySaver` 存储对话历史
- 基于 `thread_id` 隔离会话
- 支持持久化（可扩展为数据库存储）

### Streaming 实现
- 使用 `astream_events` API
- 监听 `on_chat_model_stream` 事件
- 异步生成器模式

### Structured Output 实现
- 使用提示工程引导模型生成 JSON
- 正则表达式提取 JSON 内容
- Pydantic 模型验证

### Middleware 实现
- 简单的钩子模式
- 支持 `before_invoke` 和 `after_invoke`
- 按添加顺序执行

---

## 注意事项

1. **DeepSeek 限制：**
   - 不支持原生的 `response_format`（结构化输出需要用提示工程）
   - 流式输出的事件格式可能与 OpenAI 不同

2. **性能优化：**
   - 流式传输适合长文本生成
   - 中间件会增加少量开销
   - 记忆存储在内存中，重启后丢失

3. **生产环境建议：**
   - 使用持久化的 checkpointer（如 PostgreSQL）
   - 添加错误重试机制
   - 实现更完善的速率限制
   - 添加日志和监控

---

## 扩展开发

### 添加新的结构化输出模型

```python
from pydantic import BaseModel, Field

class CustomResponse(BaseModel):
    answer: str = Field(description="回答")
    custom_field: str = Field(description="自定义字段")

# 使用
response = agent.chat_structured(
    "你的问题",
    response_model=CustomResponse
)
```

### 添加持久化记忆

```python
from langgraph.checkpoint.postgres import PostgresSaver

# 使用 PostgreSQL 存储记忆
checkpointer = PostgresSaver(connection_string="postgresql://...")

agent = create_react_agent(
    model=llm,
    tools=tools,
    checkpointer=checkpointer
)
```

---

## 参考资料

- [LangChain 官方文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [DeepSeek API 文档](https://platform.deepseek.com/docs)
