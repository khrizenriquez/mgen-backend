"""
RabbitMQ message publisher
"""
import json
import pika
import uuid
from typing import Any, Optional, Dict

from app.infrastructure.logging import get_logger
from .config import rabbitmq_config

logger = get_logger(__name__)


class MessagePublisher:
    """RabbitMQ message publisher"""

    def __init__(self):
        self.config = rabbitmq_config
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None

    def _connect(self) -> None:
        """Establish connection to RabbitMQ"""
        if self.connection and not self.connection.is_closed:
            return

        try:
            parameters = pika.ConnectionParameters(**self.config.get_connection_params())
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.config.default_exchange,
                exchange_type='direct',
                durable=True
            )

            # Declare dead letter exchange
            self.channel.exchange_declare(
                exchange=self.config.dlx_exchange,
                exchange_type='direct',
                durable=True
            )

            # Declare dead letter queue
            self.channel.queue_declare(
                queue=self.config.dlx_queue,
                durable=True
            )

            # Bind DLX queue
            self.channel.queue_bind(
                exchange=self.config.dlx_exchange,
                queue=self.config.dlx_queue,
                routing_key=self.config.dlx_queue
            )

            logger.info("Connected to RabbitMQ", exchange=self.config.default_exchange)

        except Exception as e:
            logger.error("Failed to connect to RabbitMQ", error=str(e), exc_info=True)
            raise

    def _ensure_connection(self) -> None:
        """Ensure connection is established"""
        if not self.connection or self.connection.is_closed:
            self._connect()

    def publish_message(
        self,
        message: Any,
        routing_key: str = "",
        exchange: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
        priority: int = 0
    ) -> bool:
        """
        Publish a message to RabbitMQ

        Args:
            message: Message payload (will be JSON serialized)
            routing_key: Routing key for the message
            exchange: Exchange to publish to (defaults to default exchange)
            headers: Message headers
            priority: Message priority (0-255)

        Returns:
            bool: True if message was published successfully
        """
        try:
            self._ensure_connection()

            if not self.channel:
                logger.error("No channel available for publishing")
                return False

            # Use default exchange if none specified
            target_exchange = exchange or self.config.default_exchange

            # Prepare message properties
            message_id = str(uuid.uuid4())
            properties = pika.BasicProperties(
                message_id=message_id,
                content_type='application/json',
                delivery_mode=2,  # Persistent message
                headers=headers or {},
                priority=priority,
            )

            # Serialize message to JSON
            if isinstance(message, dict):
                message_body = json.dumps(message)
            else:
                message_body = json.dumps({"data": message})

            # Publish message
            self.channel.basic_publish(
                exchange=target_exchange,
                routing_key=routing_key or self.config.default_queue,
                body=message_body,
                properties=properties
            )

            logger.info(
                "Message published successfully",
                message_id=message_id,
                exchange=target_exchange,
                routing_key=routing_key or self.config.default_queue
            )

            return True

        except Exception as e:
            logger.error(
                "Failed to publish message",
                error=str(e),
                exchange=exchange or self.config.default_exchange,
                routing_key=routing_key,
                exc_info=True
            )
            return False

    def close(self) -> None:
        """Close the connection"""
        try:
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.error("Error closing RabbitMQ connection", error=str(e))

    def __enter__(self):
        """Context manager entry"""
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Global publisher instance
message_publisher = MessagePublisher()
