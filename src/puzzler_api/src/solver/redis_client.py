import redis

from src.config import REDIS_HOST, REDIS_PORT

class RedisClient:
    def __init__(self) -> None:
        redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

    def connect(self):
        pass

    def close(self):
        pass


if __name__ == "__main__":
    pass
