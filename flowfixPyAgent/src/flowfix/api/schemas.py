from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    """聊天请求"""
    query: str
    device_name: Optional[str] = None
    user_id: Optional[int] = None
    conversation_history: Optional[list[dict]] = None


class RoutingRequest(BaseModel):
    """分流请求"""
    query: str
    device_name: Optional[str] = None
    user_id: Optional[int] = None


class DispatchRequest(BaseModel):
    """派单请求"""
    ticket_id: int
    device_type: str
    fault_type: str
    symptom: str
    priority: str = "MEDIUM"
    device_id: Optional[int] = None  # 可选，用于查询设备历史故障


class IngestRequest(BaseModel):
    """RAG入库请求"""
    ticket_id: int


class ChatResponse(BaseModel):
    """聊天响应（非流式）"""
    answer: str
    routing: dict
    references: list[dict]


class RoutingResponse(BaseModel):
    """分流响应"""
    decision: str
    reason: str
    confidence: float


class DispatchResponse(BaseModel):
    """派单响应"""
    repairman_id: int
    repairman_name: str
    reason: str
    confidence: float


class IngestResponse(BaseModel):
    """入库响应"""
    status: str
    ticket_id: int
    message: Optional[str] = None
