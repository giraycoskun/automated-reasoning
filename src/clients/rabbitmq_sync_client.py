# clients/rabbitmq_sync_client.py
"""Synchronous RabbitMQ client for solver workers."""

import pika
from typing import Optional, TYPE_CHECKING
from loguru import logger

if TYPE_CHECKING:
    import pika.adapters.blocking_connection

from clients.config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USERNAME,
    RABBITMQ_PASSWORD,
    RABBITMQ_PROBLEMS_QUEUE_NAME,
)


def create_rabbitmq_connection() -> pika.BlockingConnection:
    """
    Create a new blocking RabbitMQ connection.
    
    Returns:
        pika.BlockingConnection: A new connection to RabbitMQ.
        
    Raises:
        Exception: If connection fails.
    """
    try:
        credentials = pika.PlainCredentials(RABBITMQ_USERNAME, RABBITMQ_PASSWORD)
        parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=int(RABBITMQ_PORT),
            credentials=credentials,
            heartbeat=600,
            blocked_connection_timeout=300,
        )
        connection = pika.BlockingConnection(parameters)
        logger.info("RabbitMQ blocking connection created successfully")
        return connection
    except Exception as e:
        logger.error(f"Failed to create RabbitMQ connection: {e}")
        raise


def create_rabbitmq_channel(connection: pika.BlockingConnection) -> "pika.adapters.blocking_connection.BlockingChannel":
    """
    Create a channel from an existing RabbitMQ connection.
    
    Args:
        connection: An active RabbitMQ connection.
        
    Returns:
        pika.adapters.blocking_connection.BlockingChannel: A new channel.
        
    Raises:
        Exception: If channel creation fails.
    """
    try:
        channel = connection.channel()
        logger.info("RabbitMQ channel created successfully")
        return channel
    except Exception as e:
        logger.error(f"Failed to create RabbitMQ channel: {e}")
        raise


def setup_consumer_channel(channel: "pika.adapters.blocking_connection.BlockingChannel", prefetch_count: int = 1) -> None:
    """
    Configure a channel for consuming messages.
    
    Args:
        channel: The channel to configure.
        prefetch_count: Number of messages to prefetch (default: 1 for fair dispatch).
    """
    # Declare queue (idempotent)
    channel.queue_declare(queue=RABBITMQ_PROBLEMS_QUEUE_NAME, durable=True)
    
    # Set QoS for fair dispatch
    channel.basic_qos(prefetch_count=prefetch_count)
    
    logger.info(f"Consumer channel configured with prefetch_count={prefetch_count}")


def close_rabbitmq_connection(
    connection: Optional[pika.BlockingConnection],
    channel: Optional["pika.adapters.blocking_connection.BlockingChannel"] = None
) -> None:
    """
    Safely close RabbitMQ channel and connection.
    
    Args:
        connection: The connection to close.
        channel: Optional channel to close first.
    """
    if channel:
        try:
            channel.close()
            logger.info("RabbitMQ channel closed")
        except Exception as e:
            logger.warning(f"Error closing RabbitMQ channel: {e}")
    
    if connection:
        try:
            connection.close()
            logger.info("RabbitMQ connection closed")
        except Exception as e:
            logger.warning(f"Error closing RabbitMQ connection: {e}")
