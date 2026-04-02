# LangChain + GPT-4o-mini Agent Demo

基于 LangChain 官方文档构建的智能代理示例项目，使用 GPT-4o-mini 模型（通过灵雅中转）。

## 项目结构

```
pyAgentDemo/
├── config/              # 配置管理
│   ├── __init__.py
│   └── settings.py      # 环境变量和配置
├── tools/               # 工具定义
│   ├── __init__.py
│   └── weather_tools.py # 天气、计算、时间工具
├── agents/              # 代理定义
│   ├── __init__.py
│   ├── weather_agent.py # 基础智能助手代理
│   └── enhanced_agent.py # 增强代理（包含所有高级功能）
├── main.py              # 基础演示程序
├── demo_enhanced.py     # 增强功能演示
├── .env                 # 环境变量配置（不提交到 git）
├── .env.example         # 环境变量示例
├── ENHANCED_FEATURES.md # 增强功能详细文档
└── pyproject.toml       # 项目依赖
```

## 功能特性

### 基础功能
- ✅ 环境变量管理（使用 python-dotenv）
- ✅ 模块化项目结构
- ✅ 工具调用（Tool Calling）
- ✅ 错误处理

### 增强功能
- ✅ **Short-term Memory** (短期记忆) - 使用 MemorySaver 保存对话历史
- ✅ **Streaming** (流式传输) - 实时输出 AI 响应
- ✅ **Structured Output** (结构化输出) - 原生支持，使用 Pydantic 模型
- ✅ **Middleware** (中间件) - 预构建和自定义中间件支持

## 快速开始

### 1. 配置环境变量

复制 `.env.example` 为 `.env` 并填入你的 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.lingyaai.cn/v1
OPENAI_MODEL=gpt-4o-mini
```

### 2. 安装依赖

```bash
uv sync
```

## 演示程序

项目包含三个演示程序，展示不同级别的功能：

### 1. 基础演示（main.py）
```bash
uv run main.py
```

展示功能：
- 基础对话
- 工具调用
- 对话记忆

### 2. 增强功能演示（demo_enhanced.py）
```bash
uv run demo_enhanced.py
```

展示功能：
- Short-term Memory（短期记忆）
- Streaming（流式传输）
- Structured Output（结构化输出）
- Middleware（中间件）

### 3. 高级功能演示（demo_advanced.py）
```bash
uv run demo_advanced.py
```

展示功能：
- Runtime Context（运行时上下文）
- Context Engineering（上下文工程）
- Guardrails（防护措施）
- Role-based Access Control（基于角色的访问控制）

详细文档：
- [增强功能文档](./ENHANCED_FEATURES.md)
- [高级功能文档](./ADVANCED_FEATURES.md)

## 可用工具

代理可以使用以下工具：

1. **get_weather(city)** - 查询城市天气
2. **calculate(expression)** - 计算数学表达式
3. **get_current_time()** - 获取当前时间

## 代码示例

### 基础使用

```python
from agents import WeatherAgent

# 创建代理
agent = WeatherAgent()

# 单轮对话
response = agent.chat("北京今天天气怎么样？")
print(response)

# 多轮对话（自动保持上下文）
agent.chat("帮我计算 100 + 200")
agent.chat("把刚才的结果乘以 3")  # 代理会记住之前的对话

# 清空对话历史
agent.clear_history()
```

### 增强功能使用

```python
from agents import EnhancedWeatherAgent, WeatherResponse
import asyncio

# 创建增强代理
agent = EnhancedWeatherAgent(enable_middleware=True)

# 1. 标准对话（带中间件）
response = agent.chat("北京今天天气怎么样？")

# 2. 流式传输
async def stream_demo():
    async for chunk in agent.chat_stream("介绍一下人工智能"):
        print(chunk, end="", flush=True)

asyncio.run(stream_demo())

# 3. 结构化输出
response = agent.chat_structured(
    "上海今天天气怎么样？",
    response_model=WeatherResponse
)
print(f"城市: {response.city}")
print(f"天气: {response.weather_info}")

# 4. 添加自定义中间件
class CustomMiddleware:
    def before_invoke(self, context):
        print(f"处理请求: {context.user_message}")

    def after_invoke(self, context, response):
        print(f"响应长度: {len(response)}")

agent.add_middleware(CustomMiddleware())

# 5. 获取记忆摘要
summary = agent.get_memory_summary()
print(f"对话轮数: {summary['message_count']}")
```

## 技术栈

- **LangChain** - AI 应用开发框架
- **LangGraph** - 构建有状态的多参与者应用
- **GPT-4o-mini** - OpenAI 的高性价比模型
- **灵雅 API** - OpenAI API 中转服务
- **python-dotenv** - 环境变量管理
- **uv** - Python 包管理器

## 为什么选择 GPT-4o-mini？

1. **完整功能支持** - 原生支持 structured output、streaming 等所有 LangChain 功能
2. **高性价比** - 比 GPT-4 便宜很多，适合学习和开发
3. **快速响应** - 响应速度快，用户体验好
4. **稳定可靠** - OpenAI 官方模型，质量有保证

## 扩展开发

### 添加新工具

在 `tools/weather_tools.py` 中添加新的工具函数：

```python
from langchain_core.tools import tool

@tool
def your_new_tool(param: str) -> str:
    """工具描述"""
    # 实现你的逻辑
    return "结果"

# 添加到 ALL_TOOLS 列表
ALL_TOOLS = [get_weather, calculate, get_current_time, your_new_tool]
```

### 自定义代理

修改 `agents/weather_agent.py` 或 `agents/enhanced_agent.py` 中的 `system_prompt` 来改变代理行为。

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

## 详细文档

查看 [ENHANCED_FEATURES.md](./ENHANCED_FEATURES.md) 了解所有增强功能的详细说明和使用示例。

## 注意事项

- `.env` 文件包含敏感信息，不要提交到 git
- 生产环境建议使用更安全的配置管理方案
- `calculate` 工具使用 `eval()`，生产环境应使用更安全的实现
- 记忆存储在内存中，重启后丢失（可扩展为数据库存储）

## 常见问题

**Q: 如何切换到其他模型？**

A: 修改 `.env` 文件中的 `OPENAI_MODEL`，例如：
- `gpt-4o-mini` - 高性价比
- `gpt-4o` - 更强大
- `gpt-3.5-turbo` - 更便宜

**Q: 如何使用其他 API 提供商？**

A: 修改 `.env` 文件中的 `OPENAI_API_BASE`，只要是 OpenAI 兼容的 API 都可以使用。

**Q: 如何持久化对话记忆？**

A: 将 `MemorySaver` 替换为 `PostgresSaver` 或其他持久化 checkpointer。

## 参考资料

- [LangChain 官方文档](https://python.langchain.com/)
- [LangGraph 文档](https://langchain-ai.github.io/langgraph/)
- [OpenAI API 文档](https://platform.openai.com/docs)
- [灵雅 API 文档](https://api.lingyaai.cn)

