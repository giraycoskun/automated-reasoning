from api import __version__
import uvicorn
from api.util import setup_logging
from loguru import logger

setup_logging()

logger.info(f"Starting API version {__version__}")

uvicorn.run(
        "main:app",      # module:instance
        host="127.0.0.1",
        port=3000,
        reload=True      # auto-reload in dev
    )