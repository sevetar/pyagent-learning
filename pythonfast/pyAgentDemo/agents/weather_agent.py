"""AI 代理模块

根据 LangChain 官方文档创建的代理，支持工具调用和对话记忆。
"""
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver

from config import settings
from tools import ALL_TOOLS


class WeatherAgent:
    """天气助手代理"""

    def __init__(self):
        """初始化代理"""
        # 验证配置
        settings.validate()

        # 初始化 LLM
        self.llm = ChatOpenAI(
            model=settings.OPENAI_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_API_BASE,
            temperature=settings.MODEL_TEMPERATURE,
            max_tokens=settings.MODEL_MAX_TOKENS,
            timeout=settings.MODEL_TIMEOUT,
        )

        # 定义系统提示
        system_prompt = """你是一个智能助手，可以帮助用户查询天气、进行计算和获取时间信息。

你有以下工具可以使用：
- get_weather: 查询指定城市的天气
- calculate: 计算数学表达式
- get_current_time: 获取当前时间

请根据用户的问题，智能地选择合适的工具来回答。如果不需要使用工具，可以直接回答。
回答时请保持友好和专业。"""

        # 创建内存检查点
        memory = MemorySaver()

        # 创建 React 代理
        self.agent = create_react_agent(
            model=self.llm,
            tools=ALL_TOOLS,
            checkpointer=memory,
            prompt=system_prompt
        )

        # 线程 ID（用于对话记忆）
        self.thread_id = "default_thread"

    def chat(self, message: str) -> str:
        """与代理对话

        Args:
            message: 用户消息

        Returns:
            代理回复
        """
        try:
            # 配置（包含线程 ID 用于记忆）
            config = {"configurable": {"thread_id": self.thread_id}}

            # 调用代理
            response = self.agent.invoke(
                {"messages": [("user", message)]},
                config=config
            )

            # 获取最后一条消息作为回复
            last_message = response["messages"][-1]
            return last_message.content

        except Exception as e:
            return f"发生错误：{str(e)}"

    def clear_history(self):
        """清空对话历史（通过更换线程 ID）"""
        import uuid
        self.thread_id = str(uuid.uuid4())
