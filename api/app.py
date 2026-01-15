"""API Gateway for Solver Service."""

from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
from loguru import logger

from clients import init_redis, close_redis, init_rabbitmq, close_rabbitmq
from api.config import ENVIRONMENT
from api import __version__

from api.routes.problems_routes import problems_router

logger.info("ENVIRONMENT: {env}", env=ENVIRONMENT)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_redis()
    await init_rabbitmq()
    yield
    # Shutdown
    await close_rabbitmq()
    await close_redis()


app: FastAPI = FastAPI(
    title="Automated Reasoning API",
    description="An automated reasoning API (FastAPI Framework) via IP, CSP and search algorithms.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.include_router(problems_router)


@app.get("/")
def root() -> dict:
    """Get API information and metadata.

    Returns:
        dict: Dictionary containing API name, version, description, documentation
              link, environment, developer info, and contact details.
    """
    return {
        "API Name": "Automated Reasoning API",
        "API Version": __version__,
        "Description": "An automated reasoning API (FastAPI Framework) via IP, CSP and search algorithms.",
        "Documentation": "https://giraycoskun.github.io/automated-reasoning-api/",
        "Environment": ENVIRONMENT,
        "Developer": "giraycoskun",
        "Contact": "giraycoskun.dev@gmail.com",
    }


@app.get("/ping")
async def ping() -> str:
    """Health check endpoint.

    Returns:
        str: "pong" response to indicate the API is running and healthy.
    """
    return "pong"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api.main:app", host="127.0.0.1", port=3000, reload=True)
