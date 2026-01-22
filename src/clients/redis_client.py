# fastapi_service/clients/redis_client.py
"""Async Redis client helpers for storing problems efficiently."""

from loguru import logger
from redis.asyncio import Redis
from redis.asyncio.client import PubSub

from clients.util import _deserialize_problem, _serialize_problem
from clients.config import REDIS_HOST_URL, REDIS_MAX_CONNECTIONS, REDIS_PORT, REDIS_PROBLEMS_CHANNEL_NAME
from clients.schemas.problems import Problem


redis: Redis | None = None


async def init_redis():
    global redis
    redis_url = f"redis://{REDIS_HOST_URL}:{REDIS_PORT}"
    redis = Redis.from_url(
        url=redis_url, max_connections=REDIS_MAX_CONNECTIONS, decode_responses=False
    )
    try:
        await redis.execute_command("PING")
        logger.success("Redis connected")
    except Exception as e:
        logger.error(f"Redis connection failed: {e}")


async def close_redis():
    global redis
    if redis:
        await redis.close()
        logger.info("Redis connection closed")


async def save_to_redis(key: str, value: str) -> None:
    """Save a key-value pair to Redis."""
    global redis
    if redis:
        await redis.set(key, value)
        logger.info(f"Saved to Redis: {key}")


async def save_problem_redis(problem: Problem) -> str:
    """Persist a Problem instance in Redis using msgpack.

    Args:
        problem: The Problem instance to store.

    Returns:
        str: The Redis key used (problem_id).
    """
    global redis
    if redis is None:
        raise RuntimeError("Redis is not initialized. Call init_redis() first.")

    payload = _serialize_problem(problem)
    await redis.set(problem.problem_id, payload)
    logger.info(f"Saved problem to Redis: {problem.problem_id}")
    return problem.problem_id


async def load_problem_redis(problem_id: str) -> Problem | None:
    """Retrieve a Problem payload from Redis.

    Args:
        problem_id: The UUID key used when saving the problem.

    Returns:
        dict | None: Decoded problem payload or None if missing.
    """
    global redis
    if redis is None:
        raise RuntimeError("Redis is not initialized. Call init_redis() first.")

    blob = await redis.get(problem_id)
    if blob is None:
        return None
    return _deserialize_problem(blob)


async def check_id_exists(problem_id: str) -> bool:
    """Check if a problem ID exists in Redis.

    Args:
        problem_id: The UUID key to check.
    Returns:
        bool: True if the ID exists, False otherwise.
    """
    global redis
    if redis is None:
        raise RuntimeError("Redis is not initialized. Call init_redis() first.")
    exists = await redis.exists(problem_id)
    return exists == 1


async def subscribe_to_problem_channel() -> PubSub:
    """Subscribe to a Redis channel for pub/sub.

    Returns:
        PubSub: The Redis PubSub object.
    """
    global redis
    if redis is None:
        raise RuntimeError("Redis is not initialized. Call init_redis() first.")
    pubsub = redis.pubsub()
    try:
        await pubsub.subscribe(REDIS_PROBLEMS_CHANNEL_NAME)
        logger.info(f"Subscribed to Redis channel: {REDIS_PROBLEMS_CHANNEL_NAME}")
    finally:
        await pubsub.unsubscribe(REDIS_PROBLEMS_CHANNEL_NAME)
        await pubsub.close()

    return pubsub


async def receive_message(pubsub, timeout: float) -> dict | None:
    """Receive a message from the Redis PubSub channel.

    Args:
        pubsub (PubSub): The Redis PubSub object.
        timeout (float): Time in seconds to wait for a message.

    Returns:
        dict | None: The message data or None if no message.
    """
    while True:
        message = await pubsub.get_message(
            ignore_subscribe_messages=True, timeout=timeout
        )
        if message is None:
            return None
        elif message["type"] == "message":
            return message["data"]
        else:
            continue


async def unsunscribe_and_close_pubsub(pubsub) -> None:
    """Unsubscribe from all channels and close the PubSub connection.

    Args:
        pubsub (PubSub): The Redis PubSub object.
    """
    if pubsub:
        await pubsub.unsubscribe()
        await pubsub.close()
        logger.info("Unsubscribed and closed PubSub connection")
