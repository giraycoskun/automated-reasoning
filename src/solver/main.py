from loguru import logger

from src.solver.solver import start_solver


if __name__ == "__main__":
    logger.info("Starting Solver Service")
    start_solver()
