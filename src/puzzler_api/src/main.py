from multiprocessing import Process
from loguru import logger
import uvicorn

from src.solver.solver import start_solver

if __name__ == '__main__':

    uvicorn_process = Process(target=uvicorn.run, kwargs={
                                "app":"src.api.main:app",
                                "host":"127.0.0.1",
                                "port":5000,
                                "log_level":"info"
                                        })
    logger.info("Starting Uvicorn")
    uvicorn_process.start()

    solver_process = Process(target=start_solver)
    logger.info("Starting Solver Service")
    solver_process.start()

    uvicorn_process.join()
    logger.error("Uvicorn stopped")
    solver_process.join()
    logger.error("Solver Service stopped")
