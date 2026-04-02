"""
FastAPI路由
"""
from typing import AsyncGenerator
from sse_starlette.sse import EventSourceResponse

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from flowfix.api.schemas import (
    ChatRequest,
    RoutingRequest,
    DispatchRequest,
    IngestRequest,
    RoutingResponse,
    DispatchResponse,
    IngestResponse,
)
from flowfix.rag import get_rag_answer_generator, get_rag_ingester
from flowfix.agent import get_intelligent_router, get_auto_dispatcher
from flowfix.utils import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    流式聊天接口
    先做分流决策，再根据决策返回对应响应
    """
    async def event_generator() -> AsyncGenerator[dict, None]:
        # 1. 路由决策
        router_agent = get_intelligent_router()
        routing_result = await router_agent.decide(
            query=request.query,
            device_name=request.device_name,
            user_id=request.user_id,
        )

        # 2. 根据路由决策处理
        if routing_result["decision"] == "AUTO":
            # 直接RAG回答
            rag_generator = get_rag_answer_generator()
            yield {"event": "routing", "data": routing_result}
            async for chunk in rag_generator.generate_answer_stream(
                query=request.query,
                device_name=request.device_name,
                conversation_history=request.conversation_history,
            ):
                yield {"event": "content", "data": chunk}
        elif routing_result["decision"] == "ASSIST":
            # RAG回答 + 人工确认提示
            rag_generator = get_rag_answer_generator()
            yield {"event": "routing", "data": routing_result}
            yield {"event": "content", "data": "【系统提示】AI建议已生成，请在下方确认或修改。\n\n"}
            async for chunk in rag_generator.generate_answer_stream(
                query=request.query,
                device_name=request.device_name,
                conversation_history=request.conversation_history,
            ):
                yield {"event": "content", "data": chunk}
        else:
            # MANUAL - 建议走工单流程
            yield {"event": "routing", "data": routing_result}
            yield {
                "event": "content",
                "data": "【系统提示】您的问题需要进入完整工单流程处理。\n"
                       "我们的工作人员将尽快与您联系。\n"
                       "您也可以拨打服务热线：400-xxx-xxxx",
            }

        yield {"event": "done", "data": ""}

    return EventSourceResponse(event_generator())


@router.post("/chat")
async def chat(request: ChatRequest) -> dict:
    """非流式聊天接口"""
    # 先路由
    router_agent = get_intelligent_router()
    routing_result = await router_agent.decide(
        query=request.query,
        device_name=request.device_name,
        user_id=request.user_id,
    )

    answer = ""
    references = []

    if routing_result["decision"] == "AUTO":
        rag_generator = get_rag_answer_generator()
        async for chunk in rag_generator.generate_answer_stream(
            query=request.query,
            device_name=request.device_name,
            conversation_history=request.conversation_history,
        ):
            answer += chunk
    else:
        answer = f"【{routing_result['decision']}】{routing_result['reason']}"

    return {
        "answer": answer,
        "routing": routing_result,
        "references": references,
    }


@router.post("/route")
async def route(request: RoutingRequest) -> RoutingResponse:
    """分流决策接口"""
    router_agent = get_intelligent_router()
    result = await router_agent.decide(
        query=request.query,
        device_name=request.device_name,
        user_id=request.user_id,
    )
    return RoutingResponse(**result)
router

@router.post("/dispatch")
async def dispatch(request: DispatchRequest) -> DispatchResponse:
    """自动派单接口"""
    dispatcher = get_auto_dispatcher()
    result = await dispatcher.dispatch(
        ticket_id=request.ticket_id,
        device_type=request.device_type,
        fault_type=request.fault_type,
        symptom=request.symptom,
        priority=request.priority,
    )
    return DispatchResponse(
        repairman_id=result.repairman_id,
        repairman_name=result.repairman_name,
        reason=result.reason,
        confidence=result.confidence,
    )


@router.post("/rag/ingest")
async def ingest(request: IngestRequest) -> IngestResponse:
    """RAG数据入库接口"""
    ingester = get_rag_ingester()
    result = ingester.ingest_ticket(request.ticket_id)
    return IngestResponse(
        status=result["status"],
        ticket_id=result["ticket_id"],
        message=result.get("message"),
    )


@router.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok"}
