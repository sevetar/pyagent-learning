"""
智能分流Agent
负责判断用户请求应该走AUTO/ASSIST/MANUAL路线
"""
from enum import Enum
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from flowfix.config import get_settings
from flowfix.utils import get_logger

settings = get_settings()
logger = get_logger(__name__)


class RoutingDecision(str, Enum):
    """分流决策枚举"""
    AUTO = "AUTO"      # AI可直接回复
    ASSIST = "ASSIST"  # AI给出建议，需人工确认
    MANUAL = "MANUAL"  # 进入完整工单流程


class IntelligentRouter:
    """智能分流器"""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.llm_model,
            temperature=0.3,
        )

    def get_system_prompt(self) -> str:
        """分流决策系统提示词"""
        return """你是一个工单分流决策引擎，根据用户问题判断最合适的处理路线。

用户问题可能涉及：
- 设备故障咨询
- 故障报修
- 工单进度查询
- 技术支持请求

请根据以下规则判断：

**AUTO（AI直接回复）**：
- 用户询问的是通用故障处理常识
- 问题简单明确，知识库有现成答案
- 不需要现场处理、不需要备件、不需要权限审批

**ASSIST（AI建议+人工确认）**：
- 问题需要一定专业知识
- 可能有解决方案但需要人工确认
- 需要人工判断是否需要现场处理

**MANUAL（完整工单流程）**：
- 需要现场维修处理的故障
- 需要审批流程（权限、备件、采购等）
- 涉及安全问题需要专业人员处理
- 问题复杂需要多方协调

输出格式要求：
必须输出一行纯JSON格式的决策结果，不要包含其他内容：
{"decision": "AUTO|ASSIST|MANUAL", "reason": "判断理由简述", "confidence": 0.0-1.0}

confidence表示决策置信度，低于0.7时请返回ASSIST作为保守选择。"""

    async def decide(self, query: str, device_name: Optional[str] = None, user_id: Optional[int] = None) -> dict:
        """
        做分流决策

        Returns:
            dict: 包含decision, reason, confidence
        """
        logger.info("routing_decision", query=query[:50])

        try:
            context = f"用户问题：{query}"
            if device_name:
                context += f"\n涉及设备：{device_name}"
            if user_id:
                context += f"\n用户ID：{user_id}"

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=context),
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content.strip()

            # 解析JSON响应
            import json
            try:
                result = json.loads(content)
                decision = result.get("decision", "ASSIST")
                # 验证decision有效性
                if decision not in [d.value for d in RoutingDecision]:
                    decision = RoutingDecision.ASSIST.value
                return {
                    "decision": decision,
                    "reason": result.get("reason", ""),
                    "confidence": float(result.get("confidence", 0.5)),
                }
            except json.JSONDecodeError:
                logger.warning("failed_to_parse_routing_response", content=content)
                return {
                    "decision": RoutingDecision.ASSIST.value,
                    "reason": "解析LLM响应失败，保守返回ASSIST",
                    "confidence": 0.0,
                }

        except Exception as e:
            logger.error("routing_decision_failed", error=str(e))
            return {
                "decision": RoutingDecision.MANUAL.value,
                "reason": f"决策过程异常：{str(e)}",
                "confidence": 0.0,
            }


# 全局单例
_intelligent_router = None


def get_intelligent_router() -> IntelligentRouter:
    global _intelligent_router
    if _intelligent_router is None:
        _intelligent_router = IntelligentRouter()
    return _intelligent_router
