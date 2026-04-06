"""
自动派单Agent
根据工单信息自动选择最合适的维修人员
使用 LangChain AgentExecutor 实现真正的 tool-calling agent
"""
from typing import Optional
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from flowfix.config import get_settings
from flowfix.db import get_mysql_session, Repairman
from flowfix.agent.tools import ALL_TOOLS
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
    """自动派单器 - 基于 LangChain AgentExecutor 的 tool-calling agent"""

    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.llm_model,
            temperature=0.3,
        )

        # 创建 agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个智能派单决策引擎，负责为工单选择最合适的维修人员。

你可以使用以下工具来收集信息：
1. get_device_fault_history - 查询设备历史故障记录，了解设备过往问题
2. check_repairman_realtime_load - 查询维修员实时负载情况，了解当前工作量
3. query_similar_cases - 从知识库检索相似故障案例，了解类似问题的处理经验

决策流程建议：
1. 如果提供了 device_id，先查询设备历史故障记录，了解该设备是否有反复出现的问题
2. 查询故障现象相似的历史案例，了解哪类技能的维修员更适合处理
3. 对候选维修员逐一检查实时负载，选择负载较低且技能匹配的维修员

选择维修员时请综合考虑：
- 技能匹配：维修员的技能标签是否匹配设备类型和故障类型
- 当前负载：当前负载越低的维修员越优先
- 历史效率：平均处理时长越短的维修员效率越高
- 可用状态：只选择状态为可用的维修员

最终输出格式（必须严格遵守）：
派单决策：维修员ID [ID], 姓名 [姓名]
选择理由：[详细说明为什么选择该维修员，包括工具调用获得的关键信息]
置信度：[0.0-1.0之间的数字]"""),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # 创建 agent
        self.agent = create_tool_calling_agent(self.llm, ALL_TOOLS, self.prompt)

        # 创建 agent executor
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=ALL_TOOLS,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True,
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
        device_id: Optional[int] = None,
    ) -> DispatchResult:
        """
        执行派单决策 - 使用 Agent 自主调用工具进行多步推理

        Args:
            ticket_id: 工单ID
            device_type: 设备类型
            fault_type: 故障类型
            symptom: 故障现象
            priority: 优先级
            device_id: 可选，设备ID用于查询历史故障

        Returns:
            DispatchResult: 派单结果
        """
        logger.info("dispatching_ticket", ticket_id=ticket_id, device_type=device_type)

        # 1. 获取可用维修员列表
        available_repairmen = self.get_available_repairmen(device_type)

        if not available_repairmen:
            return DispatchResult(
                repairman_id=0,
                repairman_name="",
                reason="暂无可用维修员，请人工分配",
                confidence=0.0,
            )

        repairmen_context = self.get_repairmen_context(available_repairmen)

        # 2. 构建 agent 输入
        agent_input = f"""工单信息：
- 工单ID: {ticket_id}
- 设备类型: {device_type}
- 故障类型: {fault_type}
- 故障现象: {symptom}
- 优先级: {priority}
{f'- 设备ID: {device_id}' if device_id else ''}

可用维修员列表：
{repairmen_context}

请使用工具收集必要信息，然后选择最合适的维修员。"""

        try:
            # 3. 调用 agent executor 执行多步推理
            result = await self.agent_executor.ainvoke({"input": agent_input})

            # 4. 解析 agent 输出
            output = result.get("output", "")
            logger.info("agent_output", output=output)

            # 解析输出格式
            dispatch_result = self._parse_agent_output(output, available_repairmen)

            logger.info(
                "dispatch_completed",
                ticket_id=ticket_id,
                repairman_id=dispatch_result.repairman_id,
                confidence=dispatch_result.confidence,
            )

            return dispatch_result

        except Exception as e:
            logger.error("dispatch_failed", ticket_id=ticket_id, error=str(e))

            # 降级策略：选择负载最低的维修员
            if available_repairmen:
                selected = min(available_repairmen, key=lambda r: r["current_load"])
                return DispatchResult(
                    repairman_id=selected["id"],
                    repairman_name=selected["name"],
                    reason=f"Agent执行失败，降级为负载最低策略。错误: {str(e)}",
                    confidence=0.3,
                )

            return DispatchResult(
                repairman_id=0,
                repairman_name="",
                reason=f"派单异常：{str(e)}",
                confidence=0.0,
            )

    def _parse_agent_output(self, output: str, available_repairmen: list[dict]) -> DispatchResult:
        """
        解析 agent 输出，提取派单决策

        Args:
            output: agent 的文本输出
            available_repairmen: 可用维修员列表

        Returns:
            DispatchResult: 派单结果
        """
        try:
            # 尝试从输出中提取信息
            lines = output.strip().split("\n")

            repairman_id = 0
            repairman_name = ""
            reason = ""
            confidence = 0.5

            for line in lines:
                line = line.strip()

                # 解析派单决策行
                if "派单决策" in line or "维修员ID" in line:
                    # 提取 ID
                    import re
                    id_match = re.search(r'ID[:\s]*(\d+)', line)
                    if id_match:
                        repairman_id = int(id_match.group(1))

                    # 提取姓名
                    name_match = re.search(r'姓名[:\s]*([^\s,，]+)', line)
                    if name_match:
                        repairman_name = name_match.group(1)

                # 解析选择理由
                elif "选择理由" in line or "理由" in line:
                    reason = line.split("：", 1)[-1].split(":", 1)[-1].strip()

                # 解析置信度
                elif "置信度" in line:
                    conf_match = re.search(r'(\d+\.?\d*)', line)
                    if conf_match:
                        confidence = float(conf_match.group(1))

            # 如果没有解析到 ID，尝试从可用维修员中匹配姓名
            if repairman_id == 0 and repairman_name:
                for r in available_repairmen:
                    if r["name"] == repairman_name:
                        repairman_id = r["id"]
                        break

            # 如果仍然没有解析到，使用降级策略
            if repairman_id == 0:
                logger.warning("failed_to_parse_agent_output", output=output)
                selected = min(available_repairmen, key=lambda r: r["current_load"])
                return DispatchResult(
                    repairman_id=selected["id"],
                    repairman_name=selected["name"],
                    reason=f"Agent输出解析失败，降级为负载最低策略。原始输出: {output[:100]}",
                    confidence=0.3,
                )

            # 如果没有理由，使用 agent 的完整输出
            if not reason:
                reason = output[:200]

            return DispatchResult(
                repairman_id=repairman_id,
                repairman_name=repairman_name,
                reason=reason,
                confidence=confidence,
            )

        except Exception as e:
            logger.error("parse_agent_output_failed", error=str(e), output=output)
            # 最终降级
            selected = min(available_repairmen, key=lambda r: r["current_load"])
            return DispatchResult(
                repairman_id=selected["id"],
                repairman_name=selected["name"],
                reason=f"输出解析异常，降级为负载最低策略",
                confidence=0.2,
            )


# 全局单例
_auto_dispatcher = None


def get_auto_dispatcher() -> AutoDispatcher:
    global _auto_dispatcher
    if _auto_dispatcher is None:
        _auto_dispatcher = AutoDispatcher()
    return _auto_dispatcher
