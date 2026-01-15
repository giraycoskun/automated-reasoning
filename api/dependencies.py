from api.events.result_stream import ResultStreamer
from api.repository.rabbitmq_repository import RabbitMQRepository
from api.repository.redis_repository import RedisRepository

# Singleton-like instances shared across the API service lifecycle.
rabbitmq_repository = RabbitMQRepository()
redis_repository = RedisRepository()
result_streamer = ResultStreamer()


def get_rabbitmq_repository() -> RabbitMQRepository:
    return rabbitmq_repository


def get_redis_repository() -> RedisRepository:
    return redis_repository


def get_result_streamer() -> ResultStreamer:
    return result_streamer
