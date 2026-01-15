import json
from queue import Queue
from typing import Callable

import pika
from loguru import logger

from src.config import settings


class RabbitMQRepository:
    def __init__(self) -> None:
        parameters = pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            credentials=pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password),
        )

        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()
        channel.queue_declare(queue=settings.rabbitmq_puzzle_queue_name, durable=True)
        channel.queue_declare(queue=settings.rabbitmq_result_queue_name, durable=True)
        connection.close()

        self.connections = Queue()
        for _ in range(int(settings.rabbitmq_pool_size)):
            self.connections.put(pika.BlockingConnection(parameters))

    def _get_connection(self) -> pika.BlockingConnection:
        return self.connections.get()

    def _release_connection(self, connection: pika.BlockingConnection) -> None:
        self.connections.put(connection)

    def publish_puzzle(self, payload: dict) -> None:
        connection = self._get_connection()
        channel = connection.channel()
        channel.basic_publish(
            exchange="",
            routing_key=settings.rabbitmq_puzzle_queue_name,
            body=json.dumps(payload).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        self._release_connection(connection)

    def publish_result(self, payload: dict) -> None:
        connection = self._get_connection()
        channel = connection.channel()
        channel.basic_publish(
            exchange="",
            routing_key=settings.rabbitmq_result_queue_name,
            body=json.dumps(payload).encode("utf-8"),
            properties=pika.BasicProperties(delivery_mode=2),
        )
        self._release_connection(connection)

    def consume_results(self, callback: Callable[[dict], None]) -> None:
        connection = self._get_connection()
        channel = connection.channel()
        channel.basic_qos(prefetch_count=1)
        channel.queue_declare(queue=settings.rabbitmq_result_queue_name, durable=True)

        def _on_message(ch, method, properties, body):
            try:
                payload = json.loads(body.decode("utf-8"))
            except json.JSONDecodeError:
                logger.error("Dropping malformed message from result queue: {body}", body=body)
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            try:
                callback(payload)
            finally:
                ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=settings.rabbitmq_result_queue_name, on_message_callback=_on_message, auto_ack=False)
        channel.start_consuming()
        self._release_connection(connection)

    def close(self) -> None:
        while not self.connections.empty():
            self.connections.get().close()
