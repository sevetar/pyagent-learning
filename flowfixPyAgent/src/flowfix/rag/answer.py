"""
RAG问答生成模块
"""
from typing import AsyncGenerator, Optional
import json

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from flowfix.config import get_settings
from flowfix.rag.retrieval import get_rag_retriever
from flowfix.utils import get_logger

settings = get_settings()
logger = get_logger(__name__)


class RagAnswerGenerator:
    """RAG答案生成器"""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.llm_model,
            temperature=0.7,
            streaming=True,
        )
        self.retriever = get_rag_retriever()

    def get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个专业的故障诊断助手，负责根据历史工单知识库回答用户的设备故障问题。

请遵循以下规则：
1. 基于提供的历史案例，结合用户问题，给出专业的故障诊断建议
2. 每个回答都应该包含：故障可能原因、建议的处理步骤、参考的历史案例
3. 如果历史案例不足以完全回答，请明确指出并给出通用建议
4. 回答要专业、准确，假设你是经验丰富的维修工程师
5. 注意识别用户问题的紧急程度，对于高危故障要给出警告

回答格式：
- **故障可能原因**：[分析]
- **建议处理步骤**：[步骤]
- **参考历史案例**：[案例摘要]
- **风险提示**：[如有高危因素]"""

    async def generate_answer_stream(
        self,
        query: str,
        device_name: Optional[str] = None,
        chunk_type: Optional[str] = None,
        conversation_history: Optional[list[dict]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        流式生成答案

        Args:
            query: 用户问题
            device_name: 设备名称过滤
            chunk_type: chunk类型过滤
            conversation_history: 对话历史

        Yields:
            生成的文本片段
        """
        logger.info("generating_answer", query=query[:50])

        # 1. 检索相关案例
        search_results = self.retriever.search(
            query=query,
            device_name=device_name,
            chunk_type=chunk_type,
            top_k=5,
        )

        # 2. 构建上下文
        context = self.retriever.build_context(search_results)

        # 3. 构建消息
        messages = [SystemMessage(content=self.get_system_prompt())]

        if conversation_history:
            for msg in conversation_history[-5:]:
                if msg["role"] == "user":
                    messages.append(HumanMessage(content=msg["content"]))

        user_prompt = f"用户问题：{query}\n\n相关历史案例：\n{context}" if context else f"用户问题：{query}\n\n（无相关历史案例，请基于通用知识回答）"
        messages.append(HumanMessage(content=user_prompt))

        # 4. 流式生成
        try:
            async for chunk in self.llm.astream(messages):
                if chunk.content:
                    yield chunk.content
        except Exception as e:
            logger.error("answer_generation_failed", error=str(e))
            yield f"抱歉，生成答案时出现错误：{str(e)}"

    async def generate_answer(
        self,
        query: str,
        device_name: Optional[str] = None,
        chunk_type: Optional[str] = None,
    ) -> str:
        """非流式生成答案"""
        result = []
        async for chunk in self.generate_answer_stream(query, device_name, chunk_type):
            result.append(chunk)
        return "".join(result)


# 全局单例
_rag_answer_generator = None


def get_rag_answer_generator() -> RagAnswerGenerator:
    """获取RAG答案生成器单例"""
    global _rag_answer_generator
    if _rag_answer_generator is None:
        _rag_answer_generator = RagAnswerGenerator()
    return _rag_answer_generator
