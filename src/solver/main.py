# solver_service/main.py
"""Multi-process solver service - main dispatches worker subprocesses that consume from queue."""

import signal
import multiprocessing
from typing import List
from loguru import logger

from solver.worker import Worker
from solver.config import SOLVER_NUM_WORKERS


class SolverService:
    """Main service that spawns independent worker subprocesses."""
    
    def __init__(self, num_workers: int = SOLVER_NUM_WORKERS):
        self.num_workers = num_workers
        self.workers: List[multiprocessing.Process] = []
        self.shutdown_event = multiprocessing.Event()
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.warning(f"Received signal {signum}, initiating shutdown...")
        self.shutdown_event.set()
        
    def start(self):
        """Start all worker processes."""
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info(f"Starting solver service with {self.num_workers} workers")
        
        # Spawn worker processes
        for worker_id in range(self.num_workers):
            worker = Worker(
                worker_id=worker_id,
                shutdown_event=self.shutdown_event
            )
            process = multiprocessing.Process(
                target=worker.run,
                name=f"Worker-{worker_id}"
            )
            process.start()
            self.workers.append(process)
            logger.info(f"Started worker process {worker_id} (PID: {process.pid})")
        
        # Wait for all workers to complete
        try:
            for worker in self.workers:
                worker.join()
        except KeyboardInterrupt:
            logger.warning("Keyboard interrupt received")
            self.shutdown_event.set()
            
        logger.info("All workers have stopped. Service shutdown complete.")
        
    def stop(self):
        """Stop all worker processes gracefully."""
        logger.info("Stopping all workers...")
        self.shutdown_event.set()
        
        # Give workers time to finish current tasks
        for worker in self.workers:
            worker.join(timeout=10)
            if worker.is_alive():
                logger.warning(f"Terminating worker {worker.name}")
                worker.terminate()
                worker.join()


def main():
    """Entry point for the solver service."""
    # Set multiprocessing start method
    multiprocessing.set_start_method('spawn', force=True)
    
    logger.info("=" * 60)
    logger.info("SOLVER SERVICE STARTING")
    logger.info("=" * 60)
    
    service = SolverService(num_workers=SOLVER_NUM_WORKERS)
    
    try:
        service.start()
    except Exception as e:
        logger.error(f"Fatal error in solver service: {e}")
        service.stop()
        raise
    finally:
        logger.info("Solver service terminated")


if __name__ == "__main__":
    main()