import redis.asyncio as redis
from loguru import logger

from src.api.repository.exceptions import RedisRepositoryException

class RedisRepository:
        
    def __init__(self) -> None:
        self.connection = redis.BlockingConnectionPool(max_connections=2)
        
    async def ping(self) -> None:
        conn = await self.connection.get_connection("PING")
        await conn.send_command('PING')
        result = await conn.read_response()
        logger.info("Ping successful: {res}", res=result)
        await self.connection.release(conn)

    async def create_puzzle(self, id, puzzle) -> None:
        COMMAND = []
        for key, value in puzzle.dict().items():
            COMMAND.append(key)
            COMMAND.append(value)
        logger.debug(COMMAND)
        conn = await self.connection.get_connection("HSET")
        await conn.send_command("HSET", id, *COMMAND )
        try:
            result = await conn.read_response()
            logger.info("Puzzle create succesful: {res}", res=result)
        except redis.ResponseError:
            logger.error("Puzzle create failed")
            await self.connection.release(conn)
            raise RedisRepositoryException
        await self.connection.release(conn)

    async def exists(self, id) -> bool:
        conn = await self.connection.get_connection("EXISTS")
        await conn.send_command('EXISTS', id)
        result = await conn.read_response()
        logger.debug("Puzzle exists: {res}", res=result)
        await self.connection.release(conn)
        return bool(result)
    