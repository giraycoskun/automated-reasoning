# api/config.py
from dotenv import load_dotenv
from zoneinfo import ZoneInfo
import os
load_dotenv()

TIMEZONE= ZoneInfo(os.getenv("TIMEZONE", "Europe/Berlin"))

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
RABBITMQ_PORT = os.getenv("RABBITMQ_PORT", "5672")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USER", "dev")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "dev")
RABBITMQ_POOL_SIZE = os.getenv("RABBITMQ_POOL_SIZE", "10")
RABBITMQ_PROBLEMS_QUEUE_NAME = os.getenv("RABBITMQ_PROBLEMS_QUEUE_NAME", "problems_queue")
RABBITMQ_SOLUTIONS_QUEUE_NAME = os.getenv("RABBITMQ_RESULT_QUEUE_NAME", "result_queue")

REDIS_HOST_URL = os.getenv("REDIS_HOST_URL", "localhost")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "10"))
REDIS_PROBLEMS_CHANNEL_NAME = os.getenv("REDIS_PROBLEMS_CHANNEL_NAME", "problems")