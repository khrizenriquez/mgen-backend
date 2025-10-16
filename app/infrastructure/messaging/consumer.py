"""
RabbitMQ message consumer
"""
import json
import pika
import threading
import time
from typing import Any, Callable, Optional, Dict

from app.infrastructure.logging import get_logger
from .config import rabbitmq_config

logger = get_logger(__name__)


class MessageConsumer:
    """RabbitMQ message consumer"""

    def __init__(self, queue_name: str = None):
        self.config = rabbitmq_config
        self.queue_name = queue_name or self.config.default_queue
        self.connection: Optional[pika.BlockingConnection] = None
        self.channel: Optional[pika.channel.Channel] = None
        self.consumer_thread: Optional[threading.Thread] = None
        self.is_consuming = False
        self.message_handlers: Dict[str, Callable] = {}

    def _connect(self) -> None:
        """Establish connection to RabbitMQ"""
        try:
            parameters = pika.ConnectionParameters(**self.config.get_connection_params())
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare exchanges
            self.channel.exchange_declare(
                exchange=self.config.default_exchange,
                exchange_type='direct',
                durable=True
            )

            self.channel.exchange_declare(
                exchange=self.config.dlx_exchange,
                exchange_type='direct',
                durable=True
            )

            # Declare main queue with dead letter exchange
            self.channel.queue_declare(
                queue=self.queue_name,
                durable=True,
                arguments={
                    'x-dead-letter-exchange': self.config.dlx_exchange,
                    'x-dead-letter-routing-key': self.config.dlx_queue,
                    'x-message-ttl': 86400000,  # 24 hours in milliseconds
                }
            )

            # Bind queue to exchange
            self.channel.queue_bind(
                exchange=self.config.default_exchange,
                queue=self.queue_name,
                routing_key=self.queue_name
            )

            logger.info("Connected to RabbitMQ", queue=self.queue_name)

        except Exception as e:
            logger.error("Failed to connect to RabbitMQ", error=str(e), exc_info=True)
            raise

    def register_handler(self, message_type: str, handler: Callable) -> None:
        """
        Register a message handler function

        Args:
            message_type: Type of message this handler processes
            handler: Function that takes (message_data, message_properties) as arguments
        """
        self.message_handlers[message_type] = handler
        logger.info("Registered message handler", message_type=message_type)

    def _process_message(
        self,
        ch: pika.channel.Channel,
        method: pika.spec.Basic.Deliver,
        properties: pika.spec.BasicProperties,
        body: bytes
    ) -> None:
        """Process incoming message"""
        try:
            # Parse message
            message_data = json.loads(body.decode('utf-8'))

            # Extract message type from headers or body
            message_type = (
                properties.headers.get('message_type') if properties.headers else None
            ) or message_data.get('type')

            if not message_type:
                logger.warning("Message without type received, skipping", message_id=properties.message_id)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Get handler for message type
            handler = self.message_handlers.get(message_type)
            if not handler:
                logger.warning("No handler found for message type", message_type=message_type)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Process message
            logger.info(
                "Processing message",
                message_type=message_type,
                message_id=properties.message_id
            )

            success = handler(message_data, properties)

            if success:
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(
                    "Message processed successfully",
                    message_type=message_type,
                    message_id=properties.message_id
                )
            else:
                # Reject message and let it go to dead letter queue
                ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
                logger.error(
                    "Message processing failed, sent to DLQ",
                    message_type=message_type,
                    message_id=properties.message_id
                )

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in message", error=str(e), message_id=properties.message_id)
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(
                "Error processing message",
                error=str(e),
                message_id=properties.message_id,
                exc_info=True
            )
            ch.basic_reject(delivery_tag=method.delivery_tag, requeue=False)

    def _consume_messages(self) -> None:
        """Consume messages from queue"""
        while self.is_consuming:
            try:
                self._connect()

                if not self.channel:
                    logger.error("No channel available for consuming")
                    time.sleep(5)
                    continue

                # Set up quality of service
                self.channel.basic_qos(prefetch_count=1)

                # Start consuming
                self.channel.basic_consume(
                    queue=self.queue_name,
                    on_message_callback=self._process_message
                )

                logger.info("Started consuming messages", queue=self.queue_name)
                self.channel.start_consuming()

            except pika.exceptions.ConnectionClosedByBroker:
                logger.warning("Connection closed by broker, retrying...")
                time.sleep(5)
            except pika.exceptions.AMQPChannelError as e:
                logger.error("Channel error", error=str(e), exc_info=True)
                time.sleep(5)
            except pika.exceptions.AMQPConnectionError as e:
                logger.error("Connection error", error=str(e), exc_info=True)
                time.sleep(5)
            except Exception as e:
                logger.error("Unexpected error in consumer", error=str(e), exc_info=True)
                time.sleep(5)

    def start_consuming(self) -> None:
        """Start consuming messages in a background thread"""
        if self.is_consuming:
            logger.warning("Consumer is already running")
            return

        self.is_consuming = True
        self.consumer_thread = threading.Thread(target=self._consume_messages, daemon=True)
        self.consumer_thread.start()

        logger.info("Message consumer started", queue=self.queue_name)

    def stop_consuming(self) -> None:
        """Stop consuming messages"""
        self.is_consuming = False

        try:
            if self.channel:
                self.channel.stop_consuming()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
        except Exception as e:
            logger.error("Error stopping consumer", error=str(e))

        logger.info("Message consumer stopped", queue=self.queue_name)

    def __enter__(self):
        """Context manager entry"""
        self.start_consuming()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_consuming()
