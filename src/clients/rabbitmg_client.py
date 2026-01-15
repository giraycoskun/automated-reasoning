# clients/rabbitmq_client.py
"""RabbitMQ async client for puzzle job queuing."""

import aio_pika
from typing import Optional
from loguru import logger
from clients.config import RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_PROBLEMS_QUEUE_NAME, RABBITMQ_USERNAME, RABBITMQ_PASSWORD
from clients.schemas.problems import Problem
from clients.util import _serialize_problem

connection: Optional[aio_pika.RobustConnection] = None
channel: Optional[aio_pika.RobustChannel] = None


async def init_rabbitmq() -> None:
    """Initialize RabbitMQ connection and declare queue."""
    global connection, channel
    try:
        rabbitmq_url = f"amqp://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
        connection = await aio_pika.connect_robust(rabbitmq_url) # type: ignore
        channel = await connection.channel() # type: ignore
        await channel.declare_queue(RABBITMQ_PROBLEMS_QUEUE_NAME, durable=True) # type: ignore
        logger.success("RabbitMQ connected successfully")
    except Exception as e:
        logger.error("RabbitMQ connection failed: {}", str(e))
        raise

async def close_rabbitmq() -> None:
    """Close RabbitMQ connection.
    
    Raises:
        Exception: If closing the connection fails.
    """
    global connection, channel
    try:
        if channel:
            await channel.close()
        if connection:
            await connection.close()
        logger.info("RabbitMQ closed successfully")
    except Exception as e:
        logger.error("Error closing RabbitMQ: {error}", error=str(e))
        raise


async def enqueue_problem(problem: Problem) -> None:
    """Publish a Problem instance to the queue using msgpack serialization.
    
    Args:
        problem: The Problem instance to enqueue.
        
    Raises:
        RuntimeError: If channel is not initialized.
        Exception: If publishing fails.
    """
    global channel
    if channel is None:
        raise RuntimeError("RabbitMQ channel not initialized. Call init_rabbitmq() first.")
    
    try:
        payload = _serialize_problem(problem)
        await channel.default_exchange.publish(
            aio_pika.Message(body=payload),
            routing_key=RABBITMQ_PROBLEMS_QUEUE_NAME
        )
        logger.info("Problem object enqueued: {problem_id}", problem_id=problem.problem_id)
    except Exception as e:
        logger.error("Error enqueuing problem object: {error}", error=str(e))
        raise
