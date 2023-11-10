from multiprocessing import Process, cpu_count, current_process
import pika
from loguru import logger
from time import sleep

from src.config import ENVIRONMENT, SOLVER_WORKER_SIZE, RABBITMQ_HOST, RABBITMQ_PORT, RABBITMQ_USER, RABBITMQ_PASSWORD, RABBITMQ_PUZZLE_QUEUE_NAME, RABBITMQ_RESULT_QUEUE_NAME

def start_solver():
    logger.info("Environment: {env}", env=ENVIRONMENT)
    logger.info("Starting Solver Service")

    processes = []
    for _ in range(int(SOLVER_WORKER_SIZE)):
        p = Process(target=puzzle_consumer)
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    logger.error("Solver Service stopped")

def puzzle_consumer():
    
    logger.info("Solver Worker started {pid}", pid=current_process().name)
    parameters = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
        )
    
    while True:
        try:
            connection = pika.BlockingConnection(parameters)
            break
        except pika.exceptions.AMQPConnectionError:
            logger.error("AMQP Connection error: Solver ID: {id}", id=current_process().name)
            sleep(10)

        
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)
    channel.queue_declare(queue=RABBITMQ_PUZZLE_QUEUE_NAME, durable=True)
    channel.basic_consume(queue=RABBITMQ_PUZZLE_QUEUE_NAME, on_message_callback=callback, auto_ack=True)

    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        channel.stop_consuming()

    connection.close()

def callback(ch, method, properties, body):
    logger.info("ch: {ch}", ch=ch)
    logger.info("method: {method}", method=method)
    logger.info("properties: {properties}", properties=properties)

    puzzle_id = body.decode("utf-8")
    logger.info("Solver Worker {pid} received puzzle {puzzle}", pid=current_process().name, puzzle=puzzle_id)
    
    #ch.basic_publish(exchange='', routing_key=RABBITMQ_RESULT_QUEUE_NAME, body=body)
    
    logger.info("Solver Worker finished {pid}", pid=current_process().name)

def solve_puzzle(puzzle):
    logger.info("Solving puzzle {puzzle}", puzzle=puzzle)
    return puzzle

def result_producer():
    pass

if __name__ == "__main__":
    start_solver()