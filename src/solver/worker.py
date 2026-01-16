# solver_service/worker.py
"""Worker subprocess that consumes problems from RabbitMQ and writes solutions to Redis."""

import pika
import redis
from multiprocessing.synchronize import Event as EventType
from typing import Optional, TYPE_CHECKING
from loguru import logger

from clients.schemas.problems import ProblemName, ProblemStatus, ProblemType
from clients.schemas.solutions import Solution
from solver.models.sudoku import SudokuProblemModel
from solver.services.ip import IPSolverService

if TYPE_CHECKING:
    import pika.adapters.blocking_connection

from clients.config import RABBITMQ_PROBLEMS_QUEUE_NAME
from clients.util import _deserialize_problem
from clients.rabbitmq_sync_client import (
    create_rabbitmq_connection,
    create_rabbitmq_channel,
    setup_consumer_channel,
    close_rabbitmq_connection,
)
from clients.redis_sync_client import (
    create_redis_client,
    save_solution_to_redis,
    close_redis_client,
)

ProblemModelMap = {
    ProblemType.IP: {
        "model": {
            ProblemName.SUDOKU: SudokuProblemModel,
            # Add other IP problem models here
        },
        "solver": IPSolverService,
    },
    # Add other problem types and their models here
}

class Worker:
    """Worker subprocess that independently consumes problems and writes solutions."""
    
    def __init__(self, worker_id: int, shutdown_event: EventType):
        self.worker_id = worker_id
        self.shutdown_event = shutdown_event
        self.rabbitmq_connection: Optional[pika.BlockingConnection] = None
        self.rabbitmq_channel: Optional["pika.adapters.blocking_connection.BlockingChannel"] = None
        self.redis_client: Optional[redis.Redis] = None  # type: ignore
        
    def run(self):
        """Main entry point for the worker subprocess."""
        logger.info(f"Worker {self.worker_id} starting...")
        
        try:
            self._initialize()
            self._consume_messages()
        except KeyboardInterrupt:
            logger.info(f"Worker {self.worker_id} interrupted")
        except Exception as e:
            logger.error(f"Worker {self.worker_id} crashed: {e}")
            raise
        finally:
            self._cleanup()
            logger.info(f"Worker {self.worker_id} stopped")
            
    def _initialize(self):
        """Initialize Redis and RabbitMQ connections for this subprocess."""
        try:
            # Initialize Redis client (each worker gets its own connection)
            self.redis_client = create_redis_client()
            
            # Initialize RabbitMQ connection and channel (each worker gets its own)
            self.rabbitmq_connection = create_rabbitmq_connection()
            self.rabbitmq_channel = create_rabbitmq_channel(self.rabbitmq_connection)
            
            # Configure channel for consuming with fair dispatch
            setup_consumer_channel(self.rabbitmq_channel, prefetch_count=1)
            
            logger.success(f"Worker {self.worker_id} initialized successfully")
        except Exception as e:
            logger.error(f"Worker {self.worker_id} initialization failed: {e}")
            raise
            
    def _consume_messages(self):
        """Consume messages from RabbitMQ queue."""
        if self.rabbitmq_channel is None:
            raise RuntimeError("RabbitMQ channel not initialized")
            
        logger.info(f"Worker {self.worker_id} waiting for messages...")
        
        # Set up consumer callback
        def callback(ch, method, properties, body):
            # Check if shutdown was requested
            if self.shutdown_event.is_set():
                logger.info(f"Worker {self.worker_id} received shutdown signal")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                ch.stop_consuming()
                return
                
            try:
                self._process_message(body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Worker {self.worker_id} error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
        
        # Start consuming
        self.rabbitmq_channel.basic_consume(
            queue=RABBITMQ_PROBLEMS_QUEUE_NAME,
            on_message_callback=callback
        )
        
        try:
            self.rabbitmq_channel.start_consuming()
        except KeyboardInterrupt:
            self.rabbitmq_channel.stop_consuming()
                    
    def _process_message(self, body: bytes):
        """Process a single message from the queue."""
        try:
            # Deserialize problem
            problem = _deserialize_problem(body)
            logger.info(
                f"Worker {self.worker_id} processing problem {problem.problem_id} "
                f"(type: {problem.problem_type})"
            )

            # logger.debug(f"Worker {self.worker_id} deserialized problem: {problem}")
            
            # Solve the problem
            solution = self._solve(problem)
            
            # Store solution in Redis
            if solution:
                self._store_solution(solution)
                logger.success(
                    f"Worker {self.worker_id} solved problem {problem.problem_id} with status {solution.status}"
                )
            else:
                logger.warning(
                    f"Worker {self.worker_id} could not solve problem {problem.problem_id}"
                )
                
        except Exception as e:
            logger.error(
                f"Worker {self.worker_id} failed to process message: {e}"
            )
            raise
                
    def _store_solution(self, solution: Solution):
        """Store the solution in Redis."""
        if self.redis_client is None:
            raise RuntimeError("Redis not initialized")
        
        save_solution_to_redis(self.redis_client, solution)
        
    def _cleanup(self):
        """Clean up resources."""
        logger.info(f"Worker {self.worker_id} cleaning up...")
        
        close_rabbitmq_connection(self.rabbitmq_connection, self.rabbitmq_channel)
        close_redis_client(self.redis_client)
        
        logger.info(f"Worker {self.worker_id} cleanup complete")

    def _solve(self, problem) -> Solution:
        try:
            problem_type = ProblemModelMap[problem.problem_type]
            problem_model = problem_type["model"].get(problem.problem_name)
            solver_service = problem_type["solver"]()
        except KeyError:
            logger.error(
                f"Worker {self.worker_id} no model/solver for problem name: {problem.problem_name}"
            )
            return Solution(
                problem_id=problem.problem_id,
                solution_data={"error": f"No model for {problem.problem_name}"},
                status=ProblemStatus.UNSUPPORTED,
            )
        try:
            solver_problem = problem_model(problem=problem)
        except Exception as e:
            logger.error(
                f"Worker {self.worker_id} error creating model for problem {problem.problem_id}: {e}"
            )
            return Solution(
                problem_id=problem.problem_id,
                solution_data={"error": str(e)},
                status=ProblemStatus.FAILED,
            )
        try:
            solution = solver_service.solve(solver_problem)
            solution = solver_problem.write_back_solution(solution=solution)
            return solution
        except Exception as e:
            logger.error(
                f"Worker {self.worker_id} error solving problem {problem.problem_id}: {e}"
            )
            return Solution(
                problem_id=problem.problem_id,
                solution_data={"error": str(e)},
                status=ProblemStatus.FAILED,
            )