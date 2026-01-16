from  clients.rabbitmq_client import enqueue_problem
from clients.redis_client import load_problem_redis, save_problem_redis
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

