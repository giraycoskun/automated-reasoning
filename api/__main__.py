import asyncio
from contextlib import asynccontextmanager
from threading import Thread

from fastapi import FastAPI
from loguru import logger

from api.dependencies import (
    get_result_streamer,
    rabbitmq_repository,
    redis_repository,
)
from api.events.result_stream import ResultStreamer
from api.repository.models import ResultQueueMessage
from api.routes import auth, puzzle, status, subscription, user
from solver.config import settings

logger.info("ENVIRONMENT: {env}", env=settings.environment)


async def process_result_message(payload: dict, streamer: ResultStreamer) -> None:
    message = ResultQueueMessage(**payload)
    await redis_repository.upsert_fields(
        message.puzzle_id,
        {"status": message.status.value, "output": message.output},
    )
    await streamer.publish(message.puzzle_id, payload)


def start_result_listener(loop: asyncio.AbstractEventLoop, streamer: ResultStreamer) -> Thread:
    def _handle(payload: dict):
        loop.call_soon_threadsafe(asyncio.create_task, process_result_message(payload, streamer))

    listener = Thread(
        target=lambda: rabbitmq_repository.consume_results(_handle),
        daemon=True,
        name="result-listener",
    )
    listener.start()
    return listener


@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_running_loop()
    listener_thread = start_result_listener(loop, get_result_streamer())
    try:
        yield
    finally:
        logger.info("Shutting down RabbitMQ connections")
        rabbitmq_repository.close()
        listener_thread.join(timeout=1)


app = FastAPI(
    title="Puzzle Solver API",
    description="A puzzle solver api (FastAPI Framework) via CSP and search algorithms.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(status.router)
app.include_router(subscription.router)
app.include_router(user.router)
app.include_router(puzzle.router)
app.include_router(auth.router)


@app.get("/")
def root() -> dict:
    return {
        "Hello": "World",
        "API Name": "Puzzle Solver",
        "API Version": "0.1.0",
        "Description": "A puzzle solver api (FastAPI Framework) via CSP and search algorithms.",
        "Documentation": "https://giraycoskun.github.io/puzzle-solver-api/",
        "Environment": settings.environment,
        "Developer": "giraycoskun",
        "Contact": "giraycoskun.dev@gmail.com",
    }


@app.get("/ping")
async def ping() -> str:
    return "pong"
