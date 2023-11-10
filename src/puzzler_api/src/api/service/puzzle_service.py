from fastapi import Depends, HTTPException
from typing import Annotated
from loguru import logger
from uuid import UUID, uuid4

from src.api.repository.rabbitmq_repository import RabbitMQRepository
from src.api.repository.redis_repository import RedisRepository
from src.api.repository.models import Puzzle, PuzzleIn
from src.api.repository.exceptions import RedisRepositoryException

class PuzzleService:
    def __init__(self, rabbitMQ_repository: Annotated[RabbitMQRepository, Depends()], redis_repository: Annotated[RedisRepository, Depends()] ) -> None:
        self.rabbitMQ_repository = rabbitMQ_repository
        self.redis_repository = redis_repository
    
    async def create_puzzle(self, puzzle:PuzzleIn) -> bool:
        logger.info("Creating puzzle: {puzzle_name}", puzzle_name=puzzle.type)
        id = uuid4().hex
        while await self.redis_repository.exists(id):
            id = uuid4().hex
        puzzle = Puzzle(status="CREATED", output=" ", **puzzle.dict())
        try:
            await self.redis_repository.create_puzzle(id, puzzle)
        except RedisRepositoryException:
            raise HTTPException(status_code=500, detail="Puzzle creation failed")

        self.rabbitMQ_repository.publish_puzzle(id)
        