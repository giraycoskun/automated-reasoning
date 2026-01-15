# api/config.py
from dotenv import load_dotenv
import os
load_dotenv()

ENVIRONMENT = "dev"

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG")
LOG_FILE = os.getenv("LOG_FILE", "logs/app.log")
LOG_RETENTION = os.getenv("LOG_RETENTION", "7 days")
LOG_ROTATION = os.getenv("LOG_ROTATION", "10 MB")


RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")
RABBITMQ_USER = os.getenv("RABBITMQ_USER", "dev")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "dev")
RABBITMQ_POOL_SIZE = os.getenv("RABBITMQ_POOL_SIZE", "10")
RABBITMQ_PUZZLE_QUEUE_NAME = os.getenv("RABBITMQ_PUZZLE_QUEUE_NAME", "puzzle_queue")
RABBITMQ_RESULT_QUEUE_NAME = os.getenv("RABBITMQ_RESULT_QUEUE_NAME", "result_queue")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
