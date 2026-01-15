import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


def _int_from_env(name: str, default: int) -> int:
    value = os.getenv(name)
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    environment: str = os.getenv("ENVIRONMENT", "local")
    solver_worker_size: int = _int_from_env("SOLVER_WORKER_SIZE", 1)

    rabbitmq_host: str = os.getenv("RABBITMQ_HOST", "localhost")
    rabbitmq_port: int = _int_from_env("RABBITMQ_PORT", 5672)
    rabbitmq_user: str = os.getenv("RABBITMQ_USER", "guest")
    rabbitmq_password: str = os.getenv("RABBITMQ_PASSWORD", "guest")
    rabbitmq_pool_size: int = _int_from_env("RABBITMQ_POOL_SIZE", 5)
    rabbitmq_puzzle_queue_name: str = os.getenv("RABBITMQ_PUZZLE_QUEUE_NAME", "puzzle-jobs")
    rabbitmq_result_queue_name: str = os.getenv("RABBITMQ_RESULT_QUEUE_NAME", "puzzle-results")

    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = _int_from_env("REDIS_PORT", 6379)
    redis_db: int = _int_from_env("REDIS_DB", 0)


settings = Settings()
