import redis.asyncio as redis
from loguru import logger

from src.api.repository.exceptions import RedisRepositoryException
from src.config import settings


class RedisRepository:
    def __init__(self) -> None:
        self.client = redis.Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            decode_responses=True,
        )

    async def ping(self) -> None:
        result = await self.client.ping()
        logger.info("Redis ping successful: {res}", res=result)

    async def create_puzzle(self, puzzle_id: str, puzzle) -> None:
        try:
            await self.client.hset(puzzle_id, mapping=puzzle.dict())
        except redis.ResponseError as exc:  # pragma: no cover - defensive
            raise RedisRepositoryException from exc

    async def upsert_fields(self, puzzle_id: str, mapping: dict) -> None:
        try:
            await self.client.hset(puzzle_id, mapping=mapping)
        except redis.ResponseError as exc:  # pragma: no cover - defensive
            raise RedisRepositoryException from exc

    async def get_puzzle(self, puzzle_id: str) -> dict:
        return await self.client.hgetall(puzzle_id)

    async def exists(self, puzzle_id: str) -> bool:
        return bool(await self.client.exists(puzzle_id))
    