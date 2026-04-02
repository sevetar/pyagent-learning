import psycopg
from flowfix.config import get_settings

settings = get_settings()


def get_pgvector_connection():
    """获取PostgreSQL连接"""
    return psycopg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        dbname=settings.postgres_database,
    )


# SQL statements for pgvector setup
INIT_VECTOR_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS fault_knowledge (
    id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT,
    device_name TEXT,
    chunk_type VARCHAR(20),
    content TEXT,
    embedding VECTOR(1536),
    metadata JSONB,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

CREATE_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_fault_knowledge_embedding
ON fault_knowledge USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);
"""

CREATE_TICKET_ID_INDEX_SQL = """
CREATE INDEX IF NOT EXISTS idx_fault_knowledge_ticket_id
ON fault_knowledge (ticket_id);
"""

INSERT_CHUNK_SQL = """
INSERT INTO fault_knowledge (ticket_id, device_name, chunk_type, content, embedding, metadata)
VALUES (%s, %s, %s, %s, %s, %s)
ON CONFLICT (ticket_id, chunk_type)
DO UPDATE SET
    content = EXCLUDED.content,
    embedding = EXCLUDED.embedding,
    metadata = EXCLUDED.metadata,
    device_name = EXCLUDED.device_name;
"""

SEARCH_SIMILAR_SQL = """
SELECT id, ticket_id, device_name, chunk_type, content, metadata,
       1 - (embedding <=> %s::vector) AS similarity
FROM fault_knowledge
WHERE (%s::text IS NULL OR device_name = %s::text)
  AND (%s::text IS NULL OR chunk_type = %s::text)
ORDER BY embedding <=> %s::vector
LIMIT %s;
"""

CHECK_EXISTS_SQL = """
SELECT COUNT(*) FROM fault_knowledge WHERE ticket_id = %s AND chunk_type = %s;
"""


def init_vector_tables():
    """初始化向量表"""
    with get_pgvector_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(INIT_VECTOR_TABLE_SQL)
            cur.execute(CREATE_INDEX_SQL)
            cur.execute(CREATE_TICKET_ID_INDEX_SQL)
        conn.commit()
