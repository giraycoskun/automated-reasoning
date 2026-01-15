# solver_service/worker.py
"""Worker process that manages multiple solver threads."""

import asyncio
import aio_pika
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Event
from typing import Optional
from loguru import logger

from solver.engine import SolverEngine


class Worker:
    """Worker process that consumes problems and solves them using multiple threads."""
    
    def __init__(self, worker_id: int, shutdown_event: Event, threads_per_worker: int = 4):
        self.worker_id = worker_id
        self.shutdown_event = shutdown_event
        self.threads_per_worker = threads_per_worker
        self.solver_engine = SolverEngine()
        self.connection: Optional[aio_pika.RobustConnection] = None
        self.channel: Optional[aio_pika.RobustChannel] = None
        self.executor: Optional[ThreadPoolExecutor] = None
        
    def run(self):
        """Main entry point for the worker process."""
        # Configure logger for this worker
        logger.info(f"Worker {self.worker_id} starting...")
        
        # Run the async event loop
        try:
            asyncio.run(self._async_run())
        except Exception as e:
            logger.error(f"Worker {self.worker_id} crashed: {e}")
            raise
        finally:
            logger.info(f"Worker {self.worker_id} stopped")
            
    async def _async_run(self):
        """Async main loop for the worker."""
        # Initialize connections
        await self._initialize()
        
        try:
            # Start consuming messages
            await self._consume_messages()
        finally:
            await self._cleanup()
            
    async def _initialize(self):
        """Initialize Redis and RabbitMQ connections."""
        try:
            # Initialize Redis
            await init_redis()
            
            # Initialize RabbitMQ
            rabbitmq_url = f"amqp://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/"
            self.connection = await aio_pika.connect_robust(rabbitmq_url)
            self.channel = await self.connection.channel()
            
            # Set prefetch count to control how many messages this worker processes at once
            await self.channel.set_qos(prefetch_count=self.threads_per_worker)
            
            # Initialize thread pool
            self.executor = ThreadPoolExecutor(max_workers=self.threads_per_worker)
            
            logger.success(f"Worker {self.worker_id} initialized successfully")
        except Exception as e:
            logger.error(f"Worker {self.worker_id} initialization failed: {e}")
            raise
            
    async def _consume_messages(self):
        """Consume messages from RabbitMQ queue."""
        if self.channel is None:
            raise RuntimeError("Channel not initialized")
            
        # Declare queue (idempotent)
        queue = await self.channel.declare_queue(
            RABBITMQ_PROBLEMS_QUEUE_NAME,
            durable=True
        )
        
        logger.info(f"Worker {self.worker_id} waiting for messages...")
        
        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                # Check if shutdown was requested
                if self.shutdown_event.is_set():
                    logger.info(f"Worker {self.worker_id} received shutdown signal")
                    await message.reject(requeue=True)
                    break
                    
                try:
                    await self._process_message(message)
                except Exception as e:
                    logger.error(f"Worker {self.worker_id} error processing message: {e}")
                    await message.reject(requeue=True)
                    
    async def _process_message(self, message: aio_pika.IncomingMessage):
        """Process a single message from the queue."""
        async with message.process():
            try:
                # Deserialize problem
                problem = _deserialize_problem(message.body)
                logger.info(
                    f"Worker {self.worker_id} processing problem {problem.problem_id} "
                    f"(type: {problem.problem_type})"
                )
                
                # Solve the problem in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                solution = await loop.run_in_executor(
                    self.executor,
                    self.solver_engine.solve,
                    problem
                )
                
                # Store solution in Redis
                if solution:
                    await self._store_solution(problem.problem_id, solution)
                    logger.success(
                        f"Worker {self.worker_id} solved problem {problem.problem_id}"
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
                
    async def _store_solution(self, problem_id: str, solution: dict):
        """Store the solution in Redis."""
        from clients.redis_client import redis
        import msgpack
        
        if redis is None:
            raise RuntimeError("Redis not initialized")
            
        # Store solution with a key like "solution:{problem_id}"
        solution_key = f"solution:{problem_id}"
        solution_data = msgpack.packb(solution, use_bin_type=True)
        await redis.set(solution_key, solution_data)
        
        # Also update the problem status if needed
        # You might want to update the problem object in Redis to mark it as solved
        
    async def _cleanup(self):
        """Clean up resources."""
        logger.info(f"Worker {self.worker_id} cleaning up...")
        
        if self.executor:
            self.executor.shutdown(wait=True)
            
        if self.channel:
            await self.channel.close()
            
        if self.connection:
            await self.connection.close()
            
        await close_redis()
        
        logger.info(f"Worker {self.worker_id} cleanup complete")