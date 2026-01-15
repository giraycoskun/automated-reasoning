"""
Compatibility shim: re-export settings from src.config so legacy imports continue working.
Prefer importing from src.config directly in new code.
"""

from src.config import settings

# Legacy aliases for backward compatibility
ENVIRONMENT = settings.environment
SOLVER_WORKER_SIZE = settings.solver_worker_size

RABBITMQ_HOST = settings.rabbitmq_host
RABBITMQ_PORT = settings.rabbitmq_port
RABBITMQ_USER = settings.rabbitmq_user
RABBITMQ_PASSWORD = settings.rabbitmq_password
RABBITMQ_POOL_SIZE = settings.rabbitmq_pool_size
RABBITMQ_PUZZLE_QUEUE_NAME = settings.rabbitmq_puzzle_queue_name
RABBITMQ_RESULT_QUEUE_NAME = settings.rabbitmq_result_queue_name

REDIS_HOST = settings.redis_host
REDIS_PORT = settings.redis_port
