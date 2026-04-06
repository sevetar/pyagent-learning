"""
RabbitMQ消息消费者
消费工单事件，触发RAG入库
"""
import json
import pika
from pika.adapters.blocking_connection import BlockingChannel
from pika.spec import Basic, BasicProperties

from flowfix.config import get_settings
from flowfix.rag import get_rag_ingester
from flowfix.utils import get_logger

settings = get_settings()
logger = get_logger(__name__)


class TicketEventConsumer:
    """工单事件消费者"""

    def __init__(self):
        self.connection = None
        self.channel = None
        self.rag_ingester = get_rag_ingester()

    def connect(self):
        """建立RabbitMQ连接"""
        credentials = pika.PlainCredentials(
            settings.rabbitmq_user,
            settings.rabbitmq_password,
        )
        parameters = pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            virtual_host=settings.rabbitmq_vhost,
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )

        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        # 声明交换机和队列
        self.channel.exchange_declare(
            exchange="flowfix.ticket",
            exchange_type="topic",
            durable=True,
        )

        self.channel.queue_declare(queue="flowfix.rag.ingest", durable=True)

        # 绑定队列到交换机
        self.channel.queue_bind(
            exchange="flowfix.ticket",
            queue="flowfix.rag.ingest",
            routing_key="ticket.#",
        )

        logger.info("rabbitmq_connected")

    def _process_message(self, ticket_id: int, event_type: str):
        """处理消息"""
        logger.info("processing_ticket_event", ticket_id=ticket_id, event_type=event_type)
        # 只处理工单完成或状态变化事件
        if event_type in ["TICKET_CREATED", "TICKET_COMPLETED", "TICKET_UPDATED"]:
            result = self.rag_ingester.ingest_ticket(ticket_id)
            logger.info("ingest_result", ticket_id=ticket_id, result=result)

    def _on_message(
        self,
        channel: BlockingChannel,
        method: Basic.Deliver,
        properties: BasicProperties,
        body: bytes,
    ):
        """消息回调"""
        try:
            message = json.loads(body.decode("utf-8"))
            ticket_id = message.get("ticket_id")
            event_type = message.get("event_type", "")

            if not ticket_id:
                logger.warning("invalid_message_no_ticket_id", body=body)
                channel.basic_ack(delivery_tag=method.delivery_tag)
                return

            self._process_message(ticket_id, event_type)
            channel.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error("invalid_json_message", error=str(e), body=body)
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error("message_processing_failed", error=str(e))
            # 重新入队，稍后重试
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def start_consuming(self):
        """开始消费"""
        if not self.channel:
            self.connect()

        self.channel.basic_qos(prefetch_count=10)
        self.channel.basic_consume(
            queue="flowfix.rag.ingest",
            on_message_callback=self._on_message,
            auto_ack=False,
        )

        logger.info("started_consuming")
        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("stopping_consumer")
            self.channel.stop_consuming()
        finally:
            if self.connection:
                self.connection.close()

    def close(self):
        """关闭连接"""
        if self.channel:
            self.channel.close()
        if self.connection:
            self.connection.close()


# 单例
_consumer = None


def get_consumer() -> TicketEventConsumer:
    global _consumer
    if _consumer is None:
        _consumer = TicketEventConsumer()
    return _consumer


def start_consumer():
    """启动消费者的便捷函数"""
    consumer = get_consumer()
    consumer.start_consuming()
