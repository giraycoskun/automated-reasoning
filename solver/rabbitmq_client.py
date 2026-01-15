import pika
from loguru import logger
from abc import ABC, abstractmethod

from solver.config import settings

# Reference: 
# https://pika.readthedocs.io/en/stable/examples/asynchronous_consumer_example.html
# https://pika.readthedocs.io/en/stable/examples/asynchronous_publisher_example.html

#TODO: Add RabbitMQ Producer Client
#TODO: Add RabbitMQClient Error Callbacks

class RabbitMQClient(ABC):

    def __init__(self, queue) -> None:
        self.queue = queue
        self.parameters = pika.ConnectionParameters(
            host=settings.rabbitmq_host,
            port=settings.rabbitmq_port,
            credentials=pika.PlainCredentials(settings.rabbitmq_user, settings.rabbitmq_password),
            socket_timeout=None
        )

    def connect(self):
        self.connection = pika.SelectConnection(self.parameters, on_open_callback=self.on_connect)

    def on_connect(self, connection):
        logger.debug("Connected to RabbitMQ")
        channel = connection.channel(on_open_callback=self.on_channel_open)
        channel.add_on_close_callback(self.on_channel_close)

    @abstractmethod
    def on_channel_open(self, channel):
        pass

    def on_channel_close(self, channel, reason):
        logger.debug("Channel {channel} closed: {reason}", channel=channel ,reason=reason)
        self.close()
    
    def start(self):
        logger.debug("Starting RabbitMQ IOLoop")
        self.connection.ioloop.start()

    def close(self):
        logger.debug("Closing RabbitMQ IOLoop")
        if self.connection.is_closing or self.connection.is_closed:
            logger.info('Connection is closing or already closed')
        else:
            logger.info('Closing connection')
            self.connection.close()
        self.connection.ioloop.stop()


class RabbitMQConsumerClient(RabbitMQClient):
    
    def __init__(self, queue) -> None:
        super().__init__(queue)
    
    def on_channel_open(self, channel):
        self.channel = channel
        channel.basic_qos(prefetch_count=1)
        channel.queue_declare(settings.rabbitmq_puzzle_queue_name, durable=True, callback=self.on_queue_declared)

    def on_queue_declared(self, frame):
        self.channel.basic_consume(settings.rabbitmq_puzzle_queue_name, self.on_message, auto_ack=True)

    def on_message(self, channel, method, properties, body):
        logger.info("ch: {ch}", ch=channel)
        logger.info("method: {method}", method=method)
        logger.info("properties: {properties}", properties=properties)

        puzzle_id = body.decode("utf-8")
        logger.info("Received puzzle id {puzzle}", puzzle=puzzle_id)




class RabbitMQProducerClient(RabbitMQClient):

    def __init__(self, queue) -> None:
        super().__init__(queue)

    def on_channel_open(self, channel):
        self.channel = channel
        channel.queue_declare(settings.rabbitmq_result_queue_name, durable=True, callback=self.__on_queue_declared)
    
    def __on_queue_declared(self, frame):
        logger.debug("Frame: {frame}", frame=frame)
        logger.info("Queue {queue} declared", queue=settings.rabbitmq_result_queue_name)
        # self.channel.basic_publish(body="Hello World", exchange='', routing_key=RABBITMQ_RESULT_QUEUE_NAME)

if __name__ == "__main__":
    logger.debug("Starting RabbitMQ Client")
    client = RabbitMQConsumerClient('test')
    client.connect()
    client.start()
    