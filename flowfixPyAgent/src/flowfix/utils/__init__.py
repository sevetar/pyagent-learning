import structlog
from flowfix.config import get_settings

settings = get_settings()


def get_logger(name: str):
    """获取结构化日志记录器"""
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    return structlog.get_logger(name)


def get_chunk_id(ticket_id: int, chunk_type: str) -> str:
    """生成幂等chunk ID"""
    return f"{ticket_id}_{chunk_type}"
