"""增强版 AI 代理模块

包含以下高级功能：
1. Short-term memory (短期记忆)
2. Streaming (流式传输)
3. Structured output (结构化输出)
4. Middleware (中间件)
"""
from typing import AsyncIterator, Optional
from dataclasses import dataclass
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage

from config import settings
from tools import ALL_TOOLS


# ============ 结构化输出模型 ============
class WeatherResponse(BaseModel):
    """天气查询的结构化响应"""
    answer: str = Field(description="对用户问题的回答")
    city: Optional[str] = Field(default=None, description="查询的城市名称")
    weather_info: Optional[str] = Field(default=None, description="天气信息")
    suggestion: Optional[str] = Field(default=None, description="建议")


class CalculationResponse(BaseModel):
    """计算的结构化响应"""
    answer: str = Field(description="对用户问题的回答")
    expression: Optional[str] = Field(default=None, description="计算表达式")
    result: Optional[str] = Field(default=None, description="计算结果")


class GeneralResponse(BaseModel):
    """通用的结构化响应"""
    answer: str = Field(description="对用户问题的回答")
    tool_used: Optional[str] = Field(default=None, description="使用的工具名称")
    confidence: Optional[float] = Field(default=None, description="回答的置信度 (0-1)")


# ============ 中间件 ============
@dataclass
class MiddlewareContext:
    """中间件上下文"""
    user_message: str
    thread_id: str
    timestamp: str


class LoggingMiddleware:
    """日志中间件 - 记录所有请求和响应"""

    def __init__(self, verbose: bool = True):
        self.verbose = verbose

    def before_invoke(self, context: MiddlewareContext):
        """调用前执行"""
        if self.verbose:
            print(f"\n[Middleware] 收到请求: {context.user_message}")
            print(f"[Middleware] 线程ID: {context.thread_id}")
            print(f"[Middleware] 时间: {context.timestamp}")

    def after_invoke(self, context: MiddlewareContext, response: str):
        """调用后执行"""
        if self.verbose:
            print(f"[Middleware] 响应长度: {len(response)} 字符")


class RateLimitMiddleware:
    """速率限制中间件"""

    def __init__(self, max_requests: int = 10):
        self.max_requests = max_requests
        self.request_count = 0

    def before_invoke(self, context: MiddlewareContext):
        """检查速率限制"""
        self.request_count += 1
        if self.request_count > self.max_requests:
            raise Exception(f"超过速率限制: {self.max_requests} 次请求")
        print(f"[RateLimit] 请求计数: {self.request_count}/{self.max_requests}")


class EnhancedWeatherAgent:
    """增强版天气助手代理

    功能：
    - Short-term memory: 使用 MemorySaver 保存对话历史
    - Streaming: 支持流式输出
    - Structured output: 支持结构化响应
    - Middleware: 支持自定义中间件
    """

    def __init__(self, enable_middleware: bool = True):
        """初始化代理

        Args:
            enable_middleware: 是否启用中间件
        """
        settings.validate()

        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
            temperature=settings.MODEL_TEMPERATURE,
            max_tokens=settings.MODEL_MAX_TOKENS,
            timeout=settings.MODEL_TIMEOUT,
            streaming=True,  # 启用流式传输
        )

        # 系统提示
        system_prompt = """你是一个智能助手，可以帮助用户查询天气、进行计算和获取时间信息。

你有以下工具可以使用：
- get_weather: 查询指定城市的天气
- calculate: 计算数学表达式
- get_current_time: 获取当前时间

请根据用户的问题，智能地选择合适的工具来回答。如果不需要使用工具，可以直接回答。
回答时请保持友好和专业。"""

        # Short-term memory: 创建内存检查点
        self.memory = MemorySaver()

        # 创建 React 代理
        self.agent = create_react_agent(
            model=self.llm,
            tools=ALL_TOOLS,
            checkpointer=self.memory,
            prompt=system_prompt
        )

        # 线程 ID（用于对话记忆）
        self.thread_id = "default_thread"

        # Middleware: 中间件列表
        self.middlewares = []
        if enable_middleware:
            self.middlewares.append(LoggingMiddleware(verbose=True))
            self.middlewares.append(RateLimitMiddleware(max_requests=100))

    def _run_middlewares_before(self, message: str):
        """运行所有中间件的 before_invoke"""
        from datetime import datetime
        context = MiddlewareContext(
            user_message=message,
            thread_id=self.thread_id,
            timestamp=datetime.now().isoformat()
        )
        for middleware in self.middlewares:
            if hasattr(middleware, 'before_invoke'):
                middleware.before_invoke(context)

    def _run_middlewares_after(self, message: str, response: str):
        """运行所有中间件的 after_invoke"""
        from datetime import datetime
        context = MiddlewareContext(
            user_message=message,
            thread_id=self.thread_id,
            timestamp=datetime.now().isoformat()
        )
        for middleware in self.middlewares:
            if hasattr(middleware, 'after_invoke'):
                middleware.after_invoke(context, response)

    def chat(self, message: str) -> str:
        """标准对话（非流式）

        Args:
            message: 用户消息

        Returns:
            代理回复
        """
        try:
            # 运行前置中间件
            self._run_middlewares_before(message)

            config = {"configurable": {"thread_id": self.thread_id}}
            response = self.agent.invoke(
                {"messages": [("user", message)]},
                config=config
            )

            last_message = response["messages"][-1]
            result = last_message.content

            # 运行后置中间件
            self._run_middlewares_after(message, result)

            return result

        except Exception as e:
            return f"发生错误：{str(e)}"

    async def chat_stream(self, message: str) -> AsyncIterator[str]:
        """流式对话

        Args:
            message: 用户消息

        Yields:
            响应的每个部分
        """
        try:
            self._run_middlewares_before(message)

            config = {"configurable": {"thread_id": self.thread_id}}

            # 使用 astream_events 进行流式输出
            full_response = ""
            last_content = ""

            async for event in self.agent.astream_events(
                {"messages": [("user", message)]},
                config=config,
                version="v2"
            ):
                # 提取流式内容
                kind = event.get("event")
                if kind == "on_chat_model_stream":
                    content = event.get("data", {}).get("chunk", {})
                    if hasattr(content, "content") and content.content:
                        chunk = content.content
                        if chunk != last_content:
                            yield chunk
                            full_response += chunk
                            last_content = chunk

            self._run_middlewares_after(message, full_response)

        except Exception as e:
            yield f"发生错误：{str(e)}"

    def chat_structured(
        self,
        message: str,
        response_model: type[BaseModel] = GeneralResponse
    ) -> BaseModel:
        """结构化输出对话（使用原生 structured output）

        GPT-4o-mini 支持原生的结构化输出功能。

        Args:
            message: 用户消息
            response_model: 响应的 Pydantic 模型

        Returns:
            结构化的响应对象
        """
        try:
            self._run_middlewares_before(message)

            # 创建带结构化输出的 LLM
            structured_llm = self.llm.with_structured_output(response_model)

            # 构建提示
            prompt = f"""请根据以下用户消息，生成结构化的响应。

用户消息: {message}

如果需要使用工具，请先调用工具获取信息，然后生成结构化响应。"""

            # 调用 LLM
            response = structured_llm.invoke(prompt)

            self._run_middlewares_after(message, str(response))

            return response

        except Exception as e:
            # 返回错误的结构化响应
            return response_model(answer=f"发生错误：{str(e)}")

    def get_memory_summary(self) -> dict:
        """获取记忆摘要

        Returns:
            包含对话历史的字典
        """
        try:
            config = {"configurable": {"thread_id": self.thread_id}}
            state = self.agent.get_state(config)

            messages = state.values.get("messages", [])
            return {
                "thread_id": self.thread_id,
                "message_count": len(messages),
                "messages": [
                    {
                        "type": msg.__class__.__name__,
                        "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
                    }
                    for msg in messages
                ]
            }
        except Exception as e:
            return {"error": str(e)}

    def clear_history(self):
        """清空对话历史"""
        import uuid
        self.thread_id = str(uuid.uuid4())
        print(f"[Memory] 已清空历史，新线程ID: {self.thread_id}")

    def add_middleware(self, middleware):
        """添加自定义中间件

        Args:
            middleware: 中间件实例，需要实现 before_invoke 和/或 after_invoke 方法
        """
        self.middlewares.append(middleware)
        print(f"[Middleware] 已添加中间件: {middleware.__class__.__name__}")
