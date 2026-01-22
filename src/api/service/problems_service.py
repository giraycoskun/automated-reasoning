import json

from fastapi import Request
from clients.rabbitmq_client import enqueue_problem
from clients.redis_client import (
    load_problem_redis,
    save_problem_redis,
    subscribe_to_problem_channel,
    receive_message,
    unsunscribe_and_close_pubsub,
)
from clients.schemas.problems import Problem, ProblemStatus


async def get_problem(problem_id: str) -> Problem | None:
    """Create and submit a new problem to the queue."""
    # Dummy implementation for illustration purposes
    problem = await load_problem_redis(problem_id)
    if not problem:
        return None
    return problem


async def save_problem(problem: Problem) -> None:
    """Save the problem to the redis and queue."""
    await enqueue_problem(problem)
    problem.status = ProblemStatus.IN_QUEUE
    await save_problem_redis(problem)


async def event_generator(problem_id: str, request: Request, ttl_seconds: int = 300):
    """
    Generate SSE events from Redis pub/sub with TTL

    Args:
        problem_id: Unique identifier for the problem
        request: FastAPI request object to check for disconnection
        ttl_seconds: Time to live in seconds (default: 300 = 5 minutes)
    """
    # Create a new Redis connection for pubsub
    pubsub = await subscribe_to_problem_channel()

    # Send initial connection message
    yield f"data: {json.dumps({'type': 'connected', 'problem_id': problem_id, 'ttl': ttl_seconds})}\n\n"

    # Get message from Redis with timeout
    message = await receive_message(pubsub, timeout=ttl_seconds)

    if message and message["type"] == "message":
        # Send SSE event to client
        data = message["data"]
        yield f"data: {data}\n\n"
    else:
        yield f"data: {json.dumps({'type': 'timeout', 'message': 'No messages received within TTL', 'ttl': ttl_seconds})}\n\n"

    await unsunscribe_and_close_pubsub(pubsub)
