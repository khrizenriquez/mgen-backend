"""
RabbitMQ configuration
"""
import os
from typing import Optional

from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RabbitMQConfig:
    """RabbitMQ configuration class"""

    def __init__(self):
        self.host = os.getenv("RABBITMQ_HOST", "localhost")
        self.port = int(os.getenv("RABBITMQ_PORT", "5672"))
        self.username = os.getenv("RABBITMQ_USER", "guest")
        self.password = os.getenv("RABBITMQ_PASSWORD", "guest")
        self.vhost = os.getenv("RABBITMQ_VHOST", "/")

        # Build connection URL
        self.url = f"amqp://{self.username}:{self.password}@{self.host}:{self.port}{self.vhost}"

        # Queue and exchange settings
        self.default_exchange = os.getenv("RABBITMQ_DEFAULT_EXCHANGE", "donations_exchange")
        self.default_queue = os.getenv("RABBITMQ_DEFAULT_QUEUE", "donations_queue")
        self.dlx_exchange = os.getenv("RABBITMQ_DLX_EXCHANGE", "donations_dlx")
        self.dlx_queue = os.getenv("RABBITMQ_DLX_QUEUE", "donations_dlx_queue")

        # Retry settings
        self.max_retries = int(os.getenv("RABBITMQ_MAX_RETRIES", "3"))
        self.retry_delay = int(os.getenv("RABBITMQ_RETRY_DELAY", "5000"))  # milliseconds

    def get_connection_params(self) -> dict:
        """Get connection parameters for pika"""
        return {
            'host': self.host,
            'port': self.port,
            'credentials': {
                'username': self.username,
                'password': self.password,
            },
            'virtual_host': self.vhost,
        }


# Global config instance
rabbitmq_config = RabbitMQConfig()
