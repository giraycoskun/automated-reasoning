"""API Gateway for Solver Service.
"""

from fastapi import FastAPI
from loguru import logger

from api.config import ENVIRONMENT

logger.info("ENVIRONMENT: {env}", env=ENVIRONMENT)


app: FastAPI = FastAPI(
    title="Automated Reasoning API",
    description="An automated reasoning API (FastAPI Framework) via CSP and search algorithms.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/")
def root() -> dict:
    """Get API information and metadata.

    Returns:
        dict: Dictionary containing API name, version, description, documentation
              link, environment, developer info, and contact details.
    """
    return {
        "Hello": "World",
        "API Name": "Automated Reasoning API",
        "API Version": "0.1.0",
        "Description": "An automated reasoning API (FastAPI Framework) via CSP and search algorithms.",
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
