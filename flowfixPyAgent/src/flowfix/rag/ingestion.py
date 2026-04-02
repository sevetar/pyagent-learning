"""
RAG数据入库模块
负责从MySQL读取工单数据，拆分成chunk，生成embedding，写入pgvector
"""
import json
from datetime import datetime
from typing import Optional

from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from flowfix.config import get_settings
from flowfix.db import (
    get_mysql_session,
    get_pgvector_connection,
    Ticket,
    TicketProcess,
    INSERT_CHUNK_SQL,
    CHECK_EXISTS_SQL,
)
from flowfix.rag.embedding import generate_embeddings
from flowfix.utils import get_logger

settings = get_settings()
logger = get_logger(__name__)


class ChunkType:
    SYMPTOM = "symptom"
    CAUSE = "cause"
    SOLUTION = "solution"


class RagIngester:
    """RAG数据入库器"""

    def __init__(self):
        self.embedding_dim = settings.embedding_dim

    def split_ticket_to_chunks(self, ticket_data: dict, process_data: Optional[dict] = None) -> list[dict]:
        """将工单拆分为多个语义chunk"""
        chunks = []

        # 1. symptom chunk - 故障现象
        symptom = ticket_data.get("symptom")
        if symptom:
            chunks.append({
                "chunk_type": ChunkType.SYMPTOM,
                "content": symptom,
                "device_name": ticket_data.get("device_name") or "",
            })

        # 2. cause chunk - 故障原因
        if process_data and process_data.get("cause"):
            chunks.append({
                "chunk_type": ChunkType.CAUSE,
                "content": process_data["cause"],
                "device_name": ticket_data.get("device_name") or "",
            })

        # 3. solution chunk - 维修方案
        if process_data and process_data.get("solution"):
            chunks.append({
                "chunk_type": ChunkType.SOLUTION,
                "content": process_data["solution"],
                "device_name": ticket_data.get("device_name") or "",
            })

        return chunks

    def _check_chunk_exists(self, ticket_id: int, chunk_type: str) -> bool:
        """检查chunk是否已存在（幂等性保障）"""
        with get_pgvector_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(CHECK_EXISTS_SQL, (ticket_id, chunk_type))
                result = cur.fetchone()
                return result[0] > 0 if result else False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(Exception),
    )
    def _write_chunk_with_retry(self, chunk: dict, ticket_id: int, embedding: list[float], metadata: dict):
        """写入单个chunk，支持重试"""
        with get_pgvector_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    INSERT_CHUNK_SQL,
                    (
                        ticket_id,
                        chunk["device_name"],
                        chunk["chunk_type"],
                        chunk["content"],
                        f"[{','.join(str(x) for x in embedding)}]",
                        json.dumps(metadata, ensure_ascii=False),
                    ),
                )
            conn.commit()

    def ingest_ticket(self, ticket_id: int) -> dict:
        """
        入库单个工单的RAG数据

        Returns:
            dict: 入库结果，包含成功/失败状态和详情
        """
        logger.info("ingesting_ticket", ticket_id=ticket_id)

        try:
            # 1. 从MySQL读取工单数据
            with get_mysql_session() as session:
                ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
                if not ticket:
                    return {"status": "error", "message": f"Ticket {ticket_id} not found"}

                # 读取最新的处理记录
                process = (
                    session.query(TicketProcess)
                    .filter(TicketProcess.ticket_id == ticket_id)
                    .order_by(TicketProcess.create_time.desc())
                    .first()
                )

                ticket_data = {
                    "id": ticket.id,
                    "user_id": ticket.user_id,
                    "device_id": ticket.device_id,
                    "device_name": ticket.device_name,
                    "title": ticket.title,
                    "symptom": ticket.symptom,
                    "status": ticket.status,
                    "priority": ticket.priority,
                }

                process_data = None
                if process:
                    process_data = {
                        "cause": process.cause,
                        "solution": process.solution,
                    }

            # 2. 拆分成chunks
            chunks = self.split_ticket_to_chunks(ticket_data, process_data)
            if not chunks:
                logger.warning("no_chunks_to_ingest", ticket_id=ticket_id)
                return {"status": "skipped", "message": "No chunks to ingest"}

            # 3. 批量生成embeddings
            contents = [c["content"] for c in chunks]
            embeddings = generate_embeddings(contents)

            # 4. 写入pgvector
            success_count = 0
            fail_count = 0

            for chunk, embedding in zip(chunks, embeddings):
                try:
                    # 幂等检查
                    if self._check_chunk_exists(ticket_id, chunk["chunk_type"]):
                        logger.info("chunk_already_exists_skipping", ticket_id=ticket_id, chunk_type=chunk["chunk_type"])
                        success_count += 1
                        continue

                    metadata = {
                        "user_id": ticket_data["user_id"],
                        "device_id": ticket_data["device_id"],
                        "priority": ticket_data["priority"],
                        "status": ticket_data["status"],
                        "source": "mysql_ingestion",
                    }

                    self._write_chunk_with_retry(chunk, ticket_id, embedding, metadata)
                    success_count += 1
                    logger.info("chunk_written", ticket_id=ticket_id, chunk_type=chunk["chunk_type"])

                except Exception as e:
                    fail_count += 1
                    logger.error("chunk_write_failed", ticket_id=ticket_id, chunk_type=chunk["chunk_type"], error=str(e))

            return {
                "status": "success" if fail_count == 0 else "partial",
                "ticket_id": ticket_id,
                "total_chunks": len(chunks),
                "success_count": success_count,
                "fail_count": fail_count,
            }

        except Exception as e:
            logger.error("ingest_ticket_failed", ticket_id=ticket_id, error=str(e))
            return {"status": "error", "ticket_id": ticket_id, "message": str(e)}


# 全局单例
_rag_ingester = None


def get_rag_ingester() -> RagIngester:
    """获取RAG入库器单例"""
    global _rag_ingester
    if _rag_ingester is None:
        _rag_ingester = RagIngester()
    return _rag_ingester
