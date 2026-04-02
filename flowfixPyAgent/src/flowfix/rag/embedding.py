from langchain_openai import OpenAIEmbeddings
from flowfix.config import get_settings

settings = get_settings()

_embedding_instance = None


def get_embedding_model():
    """获取embedding模型单例"""
    global _embedding_instance
    if _embedding_instance is None:
        _embedding_instance = OpenAIEmbeddings(
            api_key=settings.openai_api_key,
            base_url=settings.openai_base_url,
            model=settings.embedding_model,
        )
    return _embedding_instance


async def generate_embedding(text: str) -> list[float]:
    """生成单个文本的embedding"""
    embeddings = get_embedding_model()
    return await embeddings.aembed_query(text)


def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """批量生成embedding"""
    embeddings = get_embedding_model()
    return embeddings.embed_documents(texts)
