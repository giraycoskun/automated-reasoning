import json
from multiprocessing import Process, current_process
from time import sleep

import pika
from loguru import logger

from src.api.repository.models import PuzzleStatus
from solver.config import settings
from src.solver.redis_client import RedisClient


def start_solver():
    logger.info("Environment: {env}", env=settings.environment)
    logger.info("Starting Solver Service")

    processes = []
    for _ in range(int(settings.solver_worker_size)):
        worker = Process(target=puzzle_consumer)
        worker.start()
        processes.append(worker)

    for worker in processes:
        worker.join()

    logger.error("Solver Service stopped")


def puzzle_consumer():
    logger.info("Solver Worker started {pid}", pid=current_process().name)
    parameters = pika.ConnectionParameters(
        host=settings.rabbitmq_host,
        port=settings.rabbitmq_port,
        credentials=pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password),
    )

    connection = None
    while not connection:
        try:
            connection = pika.BlockingConnection(parameters)
        except pika.exceptions.AMQPConnectionError:
            logger.error("AMQP Connection error: Solver ID: {id}", id=current_process().name)
            sleep(5)

    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)
    channel.queue_declare(queue=settings.rabbitmq_puzzle_queue_name, durable=True)
    channel.queue_declare(queue=settings.rabbitmq_result_queue_name, durable=True)

    redis_client = RedisClient()

    def _on_message(ch, method, properties, body):
        try:
            payload = json.loads(body.decode("utf-8"))
        except json.JSONDecodeError:
            logger.error("Malformed puzzle message {body}", body=body)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        puzzle_id = payload.get("puzzle_id")
        if not puzzle_id:
            logger.error("Puzzle message missing puzzle_id: {payload}", payload=payload)
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        logger.info(
            "Solver Worker {pid} received puzzle {puzzle}",
            pid=current_process().name,
            puzzle=puzzle_id,
        )

        puzzle_data = redis_client.fetch_puzzle(puzzle_id)
        if not puzzle_data:
            logger.error("Puzzle {puzzle_id} not found in Redis", puzzle_id=puzzle_id)
            redis_client.store_result(puzzle_id, PuzzleStatus.FAILED.value, "Puzzle not found")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        redis_client.store_result(puzzle_id, PuzzleStatus.IN_PROGRESS.value, None)

        try:
            output = solve_puzzle(puzzle_data)
            final_status = PuzzleStatus.SOLVED.value
        except Exception as exc:  # pragma: no cover - solver failure path
            logger.exception("Solver failed for {puzzle_id}", puzzle_id=puzzle_id)
            output = str(exc)
            final_status = PuzzleStatus.FAILED.value

        redis_client.store_result(puzzle_id, final_status, output)

        ch.basic_publish(
            exchange="",
            routing_key=settings.rabbitmq_result_queue_name,
            body=json.dumps(
                {
                    "puzzle_id": puzzle_id,
                    "status": final_status,
                    "output": output,
                }
            ).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

        logger.info("Solver Worker finished {pid}", pid=current_process().name)

    channel.basic_consume(
        queue=settings.rabbitmq_puzzle_queue_name, on_message_callback=_on_message, auto_ack=False
    )

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    connection.close()


def solve_puzzle(puzzle: dict) -> str:
    logger.info("Solving puzzle {puzzle}", puzzle=puzzle)
    # Placeholder: integrate ILP solver here.
    return puzzle.get("input", "")


if __name__ == "__main__":
    start_solver()