import redis

from src.config import settings


class RedisClient:
    def __init__(self) -> None:
        self.client = redis.Redis(
            host=settings.redis_host, port=settings.redis_port, db=settings.redis_db, decode_responses=True
        )

    def fetch_puzzle(self, puzzle_id: str) -> dict:
        return self.client.hgetall(puzzle_id)

    def store_result(self, puzzle_id: str, status: str, output: str | None = None) -> None:
        self.client.hset(puzzle_id, mapping={"status": status, "output": output})
