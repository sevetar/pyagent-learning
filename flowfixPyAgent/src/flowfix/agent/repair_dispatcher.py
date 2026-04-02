"""
自动派单Agent
根据工单信息自动选择最合适的维修人员
"""
from typing import Optional
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from flowfix.config import get_settings
from flowfix.db import get_mysql_session, Repairman
from flowfix.utils import get_logger

settings = get_settings()
logger = get_logger(__name__)


@dataclass
class DispatchResult:
    """派单结果"""
    repairman_id: int
    repairman_name: str
    reason: str
    confidence: float


class AutoDispatcher:
    """自动派单器"""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.llm_model,
            temperature=0.3,
        )

    def get_available_repairmen(self, device_type: Optional[str] = None) -> list[dict]:
        """获取可用维修员列表"""
        with get_mysql_session() as session:
            query = session.query(Repairman).filter(Repairman.is_available == "true")
            if device_type:
                # 简单过滤，实际可通过skill_tags JSON查询
                all_repairmen = query.all()
                filtered = [
                    {"id": r.id, "name": r.name, "skill_tags": r.skill_tags,
                     "current_load": r.current_load, "avg处理时长": r.avg处理时长}
                    for r in all_repairmen
                    if r.skill_tags and device_type in str(r.skill_tags)
                ]
                return filtered or list(query.limit(5))
            return [
                {"id": r.id, "name": r.name, "skill_tags": r.skill_tags,
                 "current_load": r.current_load, "avg处理时长": r.avg处理时长}
                for r in query.limit(10)
            ]

    def get_repairmen_context(self, repairmen: list[dict]) -> str:
        """构建维修员上下文"""
        if not repairmen:
            return "暂无维修员信息"

        parts = []
        for r in repairmen:
            skills = ", ".join(r["skill_tags"]) if r["skill_tags"] else "通用"
            parts.append(
                f"- 维修员ID:{r['id']}, 姓名:{r['name']}, 技能:{skills}, "
                f"当前负载:{r['current_load']}个工单, 平均处理时长:{r['avg处理时长']}分钟"
            )
        return "\n".join(parts)

    async def dispatch(
        self,
        ticket_id: int,
        device_type: str,
        fault_type: str,
        symptom: str,
        priority: str = "MEDIUM",
    ) -> DispatchResult:
        """
        执行派单决策

        Args:
            ticket_id: 工单ID
            device_type: 设备类型
            fault_type: 故障类型
            symptom: 故障现象
            priority: 优先级

        Returns:
            DispatchResult: 派单结果
        """
        logger.info("dispatching_ticket", ticket_id=ticket_id, device_type=device_type)

        # 1. 获取可用维修员
        available_repairmen = self.get_available_repairmen(device_type)

        if not available_repairmen:
            return DispatchResult(
                repairman_id=0,
                repairman_name="",
                reason="暂无可用维修员，请人工分配",
                confidence=0.0,
            )

        repairmen_context = self.get_repairmen_context(available_repairmen)

        # 2. 调用LLM做派单决策
        system_prompt = """你是一个派单决策引擎，负责为工单选择最合适的维修人员。

选择维修员时请综合考虑：
1. 技能匹配：维修员的技能标签是否匹配设备类型和故障类型
2. 当前负载：当前负载越低的维修员越优先
3. 历史效率：平均处理时长越短的维修员效率越高
4. 可用状态：只选择状态为可用的维修员

请从提供的维修员列表中选择最合适的一位，并说明理由。

输出格式（必须是纯JSON）：
{"repairman_id": ID数字, "repairman_name": "姓名", "reason": "选择理由", "confidence": 0.0-1.0}"""

        user_prompt = f"""工单信息：
- 工单ID: {ticket_id}
- 设备类型: {device_type}
- 故障类型: {fault_type}
- 故障现象: {symptom}
- 优先级: {priority}

可用维修员：
{repairmen_context}"""

        try:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt),
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content.strip()

            # 解析JSON响应
            import json
            try:
                result = json.loads(content)
                return DispatchResult(
                    repairman_id=int(result.get("repairman_id", 0)),
                    repairman_name=result.get("repairman_name", ""),
                    reason=result.get("reason", ""),
                    confidence=float(result.get("confidence", 0.5)),
                )
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning("failed_to_parse_dispatch_response", content=content, error=str(e))
                # 降级：选择负载最低的维修员
                if available_repairmen:
                    selected = min(available_repairmen, key=lambda r: r["current_load"])
                    return DispatchResult(
                        repairman_id=selected["id"],
                        repairman_name=selected["name"],
                        reason="LLM解析失败，降级为负载最低策略",
                        confidence=0.3,
                    )
                return DispatchResult(0, "", "无可用维修员", 0.0)

        except Exception as e:
            logger.error("dispatch_failed", ticket_id=ticket_id, error=str(e))
            return DispatchResult(
                repairman_id=0,
                repairman_name="",
                reason=f"派单异常：{str(e)}",
                confidence=0.0,
            )


# 全局单例
_auto_dispatcher = None


def get_auto_dispatcher() -> AutoDispatcher:
    global _auto_dispatcher
    if _auto_dispatcher is None:
        _auto_dispatcher = AutoDispatcher()
    return _auto_dispatcher
