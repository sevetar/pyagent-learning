"""
Agent工具函数定义
为AutoDispatcher Agent提供可调用的工具
"""
from typing import Optional
from langchain_core.tools import tool

from flowfix.db import get_mysql_session, Ticket, TicketProcess, Repairman
from flowfix.rag.retrieval import get_rag_retriever
from flowfix.utils import get_logger

logger = get_logger(__name__)


@tool
def get_device_fault_history(device_id: int, limit: int = 5) -> str:
    """
    查询设备历史故障记录

    Args:
        device_id: 设备ID
        limit: 返回记录数量，默认5条

    Returns:
        设备历史故障记录的文本描述
    """
    try:
        with get_mysql_session() as session:
            # 查询该设备的历史工单
            tickets = (
                session.query(Ticket)
                .filter(Ticket.device_id == device_id)
                .order_by(Ticket.create_time.desc())
                .limit(limit)
                .all()
            )

            if not tickets:
                return f"设备ID {device_id} 暂无历史故障记录"

            history_parts = []
            for ticket in tickets:
                # 查询该工单的处理记录
                process = (
                    session.query(TicketProcess)
                    .filter(TicketProcess.ticket_id == ticket.id)
                    .first()
                )

                history_parts.append(
                    f"工单ID: {ticket.id}\n"
                    f"  故障现象: {ticket.symptom or '未记录'}\n"
                    f"  状态: {ticket.status}\n"
                    f"  优先级: {ticket.priority}\n"
                    f"  故障原因: {process.cause if process else '未记录'}\n"
                    f"  解决方案: {process.solution if process else '未记录'}\n"
                )

            result = f"设备ID {device_id} 最近 {len(tickets)} 条故障记录：\n\n" + "\n---\n".join(history_parts)
            logger.info("device_fault_history_retrieved", device_id=device_id, count=len(tickets))
            return result

    except Exception as e:
        logger.error("get_device_fault_history_failed", device_id=device_id, error=str(e))
        return f"查询设备历史故障记录失败: {str(e)}"


@tool
def check_repairman_realtime_load(repairman_id: int) -> str:
    """
    实时查询维修员当前工单负载情况

    Args:
        repairman_id: 维修员ID

    Returns:
        维修员当前负载的详细信息
    """
    try:
        with get_mysql_session() as session:
            # 查询维修员信息
            repairman = session.query(Repairman).filter(Repairman.id == repairman_id).first()

            if not repairman:
                return f"维修员ID {repairman_id} 不存在"

            # 查询该维修员当前进行中的工单
            ongoing_tickets = (
                session.query(Ticket)
                .filter(
                    Ticket.assigned_to == repairman_id,
                    Ticket.status.in_(["ASSIGNED", "IN_PROGRESS"])
                )
                .all()
            )

            result = (
                f"维修员 {repairman.name} (ID: {repairman_id}) 当前负载情况：\n"
                f"  技能标签: {', '.join(repairman.skill_tags) if repairman.skill_tags else '通用'}\n"
                f"  当前负载: {repairman.current_load} 个工单\n"
                f"  平均处理时长: {repairman.avg处理时长} 分钟\n"
                f"  可用状态: {'可用' if repairman.is_available == 'true' else '不可用'}\n"
                f"  进行中工单数: {len(ongoing_tickets)} 个\n"
            )

            if ongoing_tickets:
                ticket_details = []
                for ticket in ongoing_tickets[:3]:  # 只显示前3个
                    ticket_details.append(
                        f"    - 工单ID {ticket.id}: {ticket.title or ticket.symptom[:30] if ticket.symptom else '无标题'}"
                    )
                result += "  进行中工单:\n" + "\n".join(ticket_details)
                if len(ongoing_tickets) > 3:
                    result += f"\n    ... 还有 {len(ongoing_tickets) - 3} 个工单"

            logger.info("repairman_load_checked", repairman_id=repairman_id, load=repairman.current_load)
            return result

    except Exception as e:
        logger.error("check_repairman_load_failed", repairman_id=repairman_id, error=str(e))
        return f"查询维修员负载失败: {str(e)}"


@tool
async def query_similar_cases(symptom: str, device_name: Optional[str] = None, top_k: int = 3) -> str:
    """
    从知识库检索相似故障案例

    Args:
        symptom: 故障现象描述
        device_name: 可选，设备名称用于过滤
        top_k: 返回相似案例数量，默认3条

    Returns:
        相似故障案例的文本描述
    """
    try:
        retriever = get_rag_retriever()

        # 检索相似案例
        results = await retriever.search(
            query=symptom,
            device_name=device_name,
            top_k=top_k
        )

        if not results:
            return f"未找到与 '{symptom[:50]}' 相似的历史案例"

        case_parts = []
        for i, result in enumerate(results):
            case_parts.append(
                f"案例 {i + 1} (相似度: {result['similarity']:.2f}):\n"
                f"  工单ID: {result['ticket_id']}\n"
                f"  设备: {result['device_name']}\n"
                f"  类型: {result['chunk_type']}\n"
                f"  内容: {result['content'][:200]}{'...' if len(result['content']) > 200 else ''}\n"
            )

        result_text = f"找到 {len(results)} 个相似案例：\n\n" + "\n---\n".join(case_parts)
        logger.info("similar_cases_retrieved", symptom=symptom[:50], count=len(results))
        return result_text

    except Exception as e:
        logger.error("query_similar_cases_failed", symptom=symptom[:50], error=str(e))
        return f"检索相似案例失败: {str(e)}"


# 导出所有工具
ALL_TOOLS = [
    get_device_fault_history,
    check_repairman_realtime_load,
    query_similar_cases,
]
