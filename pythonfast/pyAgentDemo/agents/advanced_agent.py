"""高级 AI 代理模块

展示 LangChain 的高级功能：
1. Runtime Context - 运行时上下文和依赖注入
2. Context Engineering - 上下文工程
3. Guardrails - 防护措施
"""
from typing import Optional, Any
from dataclasses import dataclass
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import SystemMessage

from config import settings
from tools import ALL_TOOLS


# ============ Runtime Context Schema ============
@dataclass
class UserContext:
    """用户运行时上下文

    包含用户的静态配置信息，在整个对话中保持不变。
    """
    user_id: str
    user_name: str
    user_role: str  # admin, editor, viewer
    language: str = "zh"
    max_tokens_per_request: int = 2000


# ============ 结构化输出模型 ============
class AnalysisResponse(BaseModel):
    """分析响应"""
    summary: str = Field(description="分析摘要")
    key_points: list[str] = Field(description="关键要点")
    confidence: float = Field(description="置信度 0-1")
    recommendations: Optional[list[str]] = Field(default=None, description="建议")


class AdvancedAgent:
    """高级代理

    展示以下功能：
    - Runtime Context: 依赖注入和用户上下文
    - Dynamic Prompts: 基于用户角色的动态提示
    - Context-aware Tools: 工具根据用户权限动态选择
    - Guardrails: 内容过滤和安全检查
    """

    def __init__(self, enable_guardrails: bool = True):
        """初始化高级代理

        Args:
            enable_guardrails: 是否启用防护措施
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
        )

        # 创建内存检查点
        self.memory = MemorySaver()

        # 线程 ID
        self.thread_id = "advanced_thread"

        # 防护措施配置
        self.enable_guardrails = enable_guardrails
        self.banned_keywords = ["hack", "exploit", "malware", "virus"]

        # 当前用户上下文（将在 invoke 时设置）
        self.current_context: Optional[UserContext] = None

    def _get_dynamic_system_prompt(self, context: UserContext) -> str:
        """根据用户上下文生成动态系统提示

        这是 Context Engineering 的核心 - 根据用户角色、语言等
        动态调整系统提示。

        Args:
            context: 用户上下文

        Returns:
            动态生成的系统提示
        """
        base_prompt = "你是一个智能助手。"

        # 根据用户角色调整提示
        if context.user_role == "admin":
            base_prompt += "\n你拥有管理员权限，可以执行所有操作。"
        elif context.user_role == "editor":
            base_prompt += "\n你拥有编辑权限，可以查询和修改数据，但不能删除。"
        elif context.user_role == "viewer":
            base_prompt += "\n你只有查看权限，只能执行只读操作。"

        # 根据语言调整
        if context.language == "en":
            base_prompt = base_prompt.replace("你是", "You are")
            base_prompt = base_prompt.replace("智能助手", "an intelligent assistant")

        # 添加用户名称
        base_prompt += f"\n\n当前用户：{context.user_name}"

        # 添加可用工具说明
        base_prompt += "\n\n你有以下工具可以使用："
        base_prompt += "\n- get_weather: 查询城市天气"
        base_prompt += "\n- calculate: 计算数学表达式"
        base_prompt += "\n- get_current_time: 获取当前时间"

        base_prompt += "\n\n请根据用户的问题，智能地选择合适的工具来回答。"
        base_prompt += "回答时请保持友好和专业。"

        return base_prompt

    def _filter_tools_by_role(self, context: UserContext) -> list:
        """根据用户角色过滤可用工具

        这是 Context Engineering 的一部分 - 动态工具选择。

        Args:
            context: 用户上下文

        Returns:
            过滤后的工具列表
        """
        # 所有角色都可以使用的基础工具
        allowed_tools = ALL_TOOLS.copy()

        # 根据角色限制工具
        if context.user_role == "viewer":
            # 查看者只能使用只读工具
            allowed_tools = [
                tool for tool in allowed_tools
                if tool.name in ["get_weather", "get_current_time"]
            ]
        elif context.user_role == "editor":
            # 编辑者可以使用大部分工具
            allowed_tools = [
                tool for tool in allowed_tools
                if tool.name != "delete_data"  # 假设有这个工具
            ]
        # admin 可以使用所有工具

        return allowed_tools

    def _apply_guardrails(self, message: str, context: UserContext) -> tuple[bool, str]:
        """应用防护措施

        检查用户输入是否包含不当内容。

        Args:
            message: 用户消息
            context: 用户上下文

        Returns:
            (是否通过检查, 错误消息)
        """
        if not self.enable_guardrails:
            return True, ""

        # 1. 内容过滤 - 检查禁用关键词
        message_lower = message.lower()
        for keyword in self.banned_keywords:
            if keyword in message_lower:
                return False, f"检测到不当内容关键词：{keyword}。请重新表述您的问题。"

        # 2. 长度检查 - 根据用户上下文限制
        max_length = context.max_tokens_per_request * 4  # 粗略估计
        if len(message) > max_length:
            return False, f"消息过长，请限制在 {max_length} 字符以内。"

        # 3. PII 检测（简化版）- 检测邮箱
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if re.search(email_pattern, message):
            # 在实际应用中，这里应该使用 PIIMiddleware 来处理
            print("[Guardrail] 检测到邮箱地址，已记录但允许继续")

        return True, ""

    def chat(
        self,
        message: str,
        context: UserContext
    ) -> str:
        """与代理对话（带运行时上下文）

        Args:
            message: 用户消息
            context: 用户运行时上下文

        Returns:
            代理回复
        """
        try:
            # 保存当前上下文
            self.current_context = context

            # 应用防护措施
            passed, error_msg = self._apply_guardrails(message, context)
            if not passed:
                return f"[Guardrail] {error_msg}"

            # 获取动态系统提示
            system_prompt = self._get_dynamic_system_prompt(context)

            # 根据角色过滤工具
            filtered_tools = self._filter_tools_by_role(context)

            # 创建代理（每次都重新创建以应用新的提示和工具）
            agent = create_react_agent(
                model=self.llm,
                tools=filtered_tools,
                checkpointer=self.memory,
                prompt=system_prompt
            )

            # 配置
            config = {"configurable": {"thread_id": self.thread_id}}

            # 调用代理
            response = agent.invoke(
                {"messages": [("user", message)]},
                config=config
            )

            # 获取回复
            last_message = response["messages"][-1]
            result = last_message.content

            # 后置防护措施 - 检查输出
            if self.enable_guardrails:
                result = self._sanitize_output(result)

            return result

        except Exception as e:
            return f"发生错误：{str(e)}"

    def _sanitize_output(self, output: str) -> str:
        """清理输出内容

        Args:
            output: 原始输出

        Returns:
            清理后的输出
        """
        # 简化版 PII 脱敏 - 隐藏邮箱
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        output = re.sub(email_pattern, '[REDACTED_EMAIL]', output)

        return output

    def chat_with_analysis(
        self,
        message: str,
        context: UserContext
    ) -> AnalysisResponse:
        """带分析的对话（结构化输出）

        Args:
            message: 用户消息
            context: 用户上下文

        Returns:
            结构化的分析响应
        """
        try:
            # 应用防护措施
            passed, error_msg = self._apply_guardrails(message, context)
            if not passed:
                return AnalysisResponse(
                    summary=f"[Guardrail] {error_msg}",
                    key_points=[],
                    confidence=0.0
                )

            # 创建带结构化输出的 LLM
            structured_llm = self.llm.with_structured_output(AnalysisResponse)

            # 构建提示
            prompt = f"""请分析以下用户消息并生成结构化响应。

用户：{context.user_name} ({context.user_role})
消息：{message}

请提供：
1. 简要摘要
2. 关键要点（列表）
3. 置信度（0-1）
4. 建议（可选）"""

            # 调用 LLM
            response = structured_llm.invoke(prompt)

            return response

        except Exception as e:
            return AnalysisResponse(
                summary=f"发生错误：{str(e)}",
                key_points=[],
                confidence=0.0
            )

    def get_context_info(self) -> dict:
        """获取当前上下文信息

        Returns:
            上下文信息字典
        """
        if not self.current_context:
            return {"error": "没有活动的上下文"}

        return {
            "user_id": self.current_context.user_id,
            "user_name": self.current_context.user_name,
            "user_role": self.current_context.user_role,
            "language": self.current_context.language,
            "guardrails_enabled": self.enable_guardrails,
            "thread_id": self.thread_id
        }

    def clear_history(self):
        """清空对话历史"""
        import uuid
        self.thread_id = str(uuid.uuid4())
        print(f"[Memory] 已清空历史，新线程ID: {self.thread_id}")
