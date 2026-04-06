"""
FlowFix AI Agent 主程序入口
"""
import asyncio
import click
from flowfix.config import get_settings
from flowfix.utils import get_logger

settings = get_settings()
logger = get_logger(__name__)


@click.group()
def cli():
    """FlowFix AI Agent 命令行工具"""
    pass


@cli.command()
@click.option("--host", default=None, help="API服务主机")
@click.option("--port", default=None, help="API服务端口")
def api(host, port):
    """启动FastAPI服务"""
    import uvicorn
    from flowfix.api import app
    h = host or settings.app_host
    p = port or settings.app_port
    logger.info("starting_api", host=h, port=p)
    uvicorn.run(app, host=h, port=p, log_level=settings.log_level.lower())


@cli.command()
def consumer():
    """启动RabbitMQ消费者"""
    from flowfix.core import start_consumer

    logger.info("starting_consumer")
    start_consumer()


@cli.command()
def init_db():
    """初始化数据库表"""
    from flowfix.db import init_mysql_tables, init_vector_tables

    logger.info("initializing_mysql_tables")
    init_mysql_tables()
    logger.info("initializing_vector_tables")
    init_vector_tables()
    logger.info("db_init_complete")


@cli.command()
@click.option("--ticket-id", required=True, type=int, help="工单ID")
def ingest_ticket(ticket_id):
    """手动入库单个工单到RAG"""
    from flowfix.rag import get_rag_ingester

    ingester = get_rag_ingester()
    result = ingester.ingest_ticket(ticket_id)
    click.echo(f"入庺结果: {result}")


if __name__ == "__main__":
    cli()
