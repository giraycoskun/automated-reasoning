from loguru import logger
import sys
from pathlib import Path

from api.config import LOG_LEVEL, LOG_FILE, LOG_ROTATION, LOG_RETENTION

def setup_logging():
    """
    Sets up Loguru logging with both stdout and file output.
    """
    # Remove default logger
    logger.remove()

    # Ensure log directory exists
    log_path = Path(LOG_FILE).parent
    log_path.mkdir(parents=True, exist_ok=True)

    # Console logging
    logger.add(
        sys.stdout,
        level=LOG_LEVEL,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
               "<level>{message}</level>"
    )

    # File logging with rotation and retention
    logger.add(
        LOG_FILE,
        level=LOG_LEVEL,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        compression="zip",  # compress old logs
        enqueue=True,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )

    logger.info("Logging is set up. Logs will be written to stdout and %s", LOG_FILE)
