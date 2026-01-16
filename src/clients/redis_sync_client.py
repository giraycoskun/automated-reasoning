# clients/redis_sync_client.py
"""Synchronous Redis client for solver workers."""

import redis
import msgpack
from typing import Optional, Any, Dict
from loguru import logger

from clients.config import REDIS_HOST_URL, REDIS_PORT
from clients.schemas.solutions import Solution


def create_redis_client() -> redis.Redis:  # type: ignore
    """
    Create a new synchronous Redis client.

    Returns:
        redis.Redis: A new Redis client instance.

    Raises:
        Exception: If connection or ping fails.
    """
    try:
        redis_url = f"redis://{REDIS_HOST_URL}:{REDIS_PORT}"
        client: redis.Redis = redis.Redis.from_url(redis_url, decode_responses=False)  # type: ignore

        # Test connection
        client.ping()
        logger.info("Redis sync client connected successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to create Redis client: {e}")
        raise


def save_solution_to_redis(
    client: redis.Redis,  # type: ignore
    solution: Solution,
) -> None:
    """
    Save a solution to Redis and update the problem with solution data.

    Args:
        client: Redis client instance.
        solution: The Solution object containing problem_id, solution_data, and status.

    Raises:
        RuntimeError: If client is None.
        Exception: If save fails.
    """
    if client is None:
        raise RuntimeError("Redis client is None")

    try:
        # Load and update the problem with solution data
        problem_bytes = client.get(solution.problem_id)
        if problem_bytes and isinstance(problem_bytes, bytes):
            from clients.util import _deserialize_problem, _serialize_problem

            problem = _deserialize_problem(problem_bytes)
            problem.solution = solution.solution_data
            problem.status = solution.status

            # Save updated problem back to Redis
            updated_problem_bytes = _serialize_problem(problem)
            client.set(solution.problem_id, updated_problem_bytes)
            logger.info(f"Problem {solution.problem_id} updated with solution")
        else:
            logger.warning(
                f"Problem {solution.problem_id} not found in Redis, only solution saved"
            )

    except Exception as e:
        logger.error(f"Failed to save solution to Redis: {e}")
        raise


def close_redis_client(client: Optional[redis.Redis]) -> None:  # type: ignore
    """
    Safely close Redis client connection.

    Args:
        client: The Redis client to close.
    """
    if client:
        try:
            client.close()
            logger.info("Redis client closed")
        except Exception as e:
            logger.warning(f"Error closing Redis client: {e}")
