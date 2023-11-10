from fastapi import FastAPI
from multiprocessing import Process
from loguru import logger
from contextlib import asynccontextmanager


from src.config import ENVIRONMENT
from src.api.routes import status, subscription, user, puzzle, auth
from src.api.repository.rabbitmq_repository import RabbitMQRepository

logger.info("ENVIRONMENT: {env}", env=ENVIRONMENT)


app = FastAPI(
    title="Puzzle Solver API",
    description="A puzzle solver api (FastAPI Framework) via CSP and search algorithms.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
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
        "Environment": ENVIRONMENT,
        "Developer": "giraycoskun",
        "Contact": "giraycoskun.dev@gmail.com"
            }

@app.get("/ping")
async def ping() -> str:
    return "pong"
