"""
RAG检索与问答模块
"""
from typing import Optional, AsyncGenerator
import json

from flowfix.config import get_settings
from flowfix.db import get_pgvector_connection, SEARCH_SIMILAR_SQL
from flowfix.rag.embedding import generate_embedding
from flowfix.utils import get_logger

settings = get_settings()
logger = get_logger(__name__)


class RagRetriever:
    """RAG检索器"""

    def __init__(self, top_k: int = 5):
        self.top_k = top_k

    async def search(
        self,
        query: str,
        device_name: Optional[str] = None,
        chunk_type: Optional[str] = None,
        top_k: Optional[int] = None,
    ) -> list[dict]:
        """
        向量检索

        Args:
            query: 查询文本
            device_name: 可选，按设备名过滤
            chunk_type: 可选，按chunk类型过滤
            top_k: 返回数量

        Returns:
            检索结果列表
        """
        try:
            query_embedding = await generate_embedding(query)
            embedding_str = f"[{','.join(str(x) for x in query_embedding)}]"

            k = top_k or self.top_k

            with get_pgvector_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        SEARCH_SIMILAR_SQL,
                        (
                            embedding_str,
                            device_name,
                            device_name,
                            chunk_type,
                            chunk_type,
                            embedding_str,
                            k,
                        ),
                    )
                    rows = cur.fetchall()

            results = []
            for row in rows:
                results.append({
                    "id": row[0],
                    "ticket_id": row[1],
                    "device_name": row[2],
                    "chunk_type": row[3],
                    "content": row[4],
                    "metadata": row[5],
                    "similarity": float(row[6]) if row[6] else 0.0,
                })

            logger.info("search_completed", query=query[:50], results_count=len(results))
            return results

        except Exception as e:
            logger.error("search_failed", query=query[:50], error=str(e))
            return []

    def build_context(self, search_results: list[dict], max_chunks: int = 5) -> str:
        """将检索结果拼接为上下文"""
        if not search_results:
            return ""

        context_parts = []
        for i, result in enumerate(search_results[:max_chunks]):
            chunk_type = result.get("chunk_type", "")
            content = result.get("content", "")
            device_name = result.get("device_name", "未知设备")
            ticket_id = result.get("ticket_id", "")

            context_parts.append(
                f"【案例{i + 1}】(工单ID: {ticket_id}, 设备: {device_name}, 类型: {chunk_type})\n{content}"
            )

        return "\n\n".join(context_parts)


# 全局单例
_rag_retriever = None


def get_rag_retriever() -> RagRetriever:
    """获取RAG检索器单例"""
    global _rag_retriever
    if _rag_retriever is None:
        _rag_retriever = RagRetriever()
    return _rag_retriever
