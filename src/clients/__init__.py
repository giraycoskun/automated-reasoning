from clients.rabbitmq_client import init_rabbitmq, close_rabbitmq
from clients.redis_client import init_redis, close_redis
from clients.rabbitmq_sync_client import (
    create_rabbitmq_connection,
    create_rabbitmq_channel,
    setup_consumer_channel,
    close_rabbitmq_connection,
)
from clients.redis_sync_client import (
    create_redis_client,
    save_solution_to_redis,
    close_redis_client,
)

__all__ = [
    # Async clients (for API service)
    "init_rabbitmq",
    "close_rabbitmq",
    "init_redis",
    "close_redis",
    # Sync clients (for solver workers)
    "create_rabbitmq_connection",
    "create_rabbitmq_channel",
    "setup_consumer_channel",
    "close_rabbitmq_connection",
    "create_redis_client",
    "save_solution_to_redis",
    "close_redis_client",
]