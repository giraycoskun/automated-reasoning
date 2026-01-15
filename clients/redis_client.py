# fastapi_service/clients/redis_client.py
"""Async Redis client helpers for storing problems efficiently."""

from loguru import logger
from redis.asyncio import Redis

from clients.util import _deserialize_problem, _serialize_problem
from clients.config import REDIS_HOST_URL, REDIS_MAX_CONNECTIONS, REDIS_PORT
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
