from uuid import uuid4
from typing import Annotated

from fastapi import Depends, HTTPException
from loguru import logger

from src.api.repository.exceptions import RedisRepositoryException
from src.api.repository.models import (
    Puzzle,
    PuzzleIn,
    PuzzleQueueMessage,
    PuzzleStatus,
)
from src.api.repository.rabbitmq_repository import RabbitMQRepository
from src.api.repository.redis_repository import RedisRepository
from src.api.dependencies import get_rabbitmq_repository, get_redis_repository


class PuzzleService:
    def __init__(
        self,
        rabbitmq_repository: Annotated[RabbitMQRepository, Depends(get_rabbitmq_repository)],
        redis_repository: Annotated[RedisRepository, Depends(get_redis_repository)],
    ) -> None:
        self.rabbitmq_repository = rabbitmq_repository
        self.redis_repository = redis_repository

    async def create_puzzle(self, puzzle: PuzzleIn) -> str:
        logger.info("Creating puzzle: {puzzle_name}", puzzle_name=puzzle.type)
        puzzle_id = uuid4().hex
        while await self.redis_repository.exists(puzzle_id):
            puzzle_id = uuid4().hex

        puzzle_record = Puzzle(status=PuzzleStatus.CREATED, output=None, **puzzle.dict())
        try:
            await self.redis_repository.create_puzzle(puzzle_id, puzzle_record)
        except RedisRepositoryException:
            raise HTTPException(status_code=500, detail="Puzzle creation failed")

        queue_message = PuzzleQueueMessage(puzzle_id=puzzle_id)
        self.rabbitmq_repository.publish_puzzle(queue_message.dict())

        return puzzle_id

    async def get_puzzle(self, puzzle_id: str) -> Puzzle | None:
        data = await self.redis_repository.get_puzzle(puzzle_id)
        if not data:
            return None
        return Puzzle(**data)
