import pika
import json
from typing import Callable, Dict
from pika.exchange_type import ExchangeType
from multiprocessing import Manager

from process_manager import (
    CommandTransferObject,
    ProcessManager,
)

from periodic_queue_listener import PeriodicQueueListener


class Decorators:
    _funcs: Dict[str, Callable] = {}

    @classmethod
    def action(cls, route):
        def decorator(func):
            cls._funcs[route] = func
        return decorator

    def __init__(self):
        super().__init__()
        parameters = pika.URLParameters('amqp://guest:guest@localhost:5672')
        self._connection = pika.BlockingConnection(parameters)
        self._channel = self._connection.channel()
        self._channel.queue_declare('test_routing_key', durable=True)
        self._channel.exchange_declare(
            exchange="test_exchange",
            durable=True,
            exchange_type=ExchangeType.topic,
        )
        self._channel.queue_bind(
            exchange="test_exchange",
            routing_key="test_routing_key",
            queue='test_routing_key',
        )
        self._init_process_manager(process_restart_period_sec = 3)

    def publish_to_rabbit(self, payload):
        self._channel.basic_publish(
            exchange='test_exchange',
            routing_key='test_routing_key',
            body=json.dumps(payload.payload),
            properties=pika.BasicProperties(
                content_type='text/plain',
                delivery_mode=pika.DeliveryMode.Transient,
            )
        )

    def _init_process_manager(self, process_restart_period_sec: int) -> None:
        """
        Подготовка очередей для взаимодействия с дочерними процессами и запуск
        потока для периодических перезапусков
        """
        self._manager = Manager()
        self._input_queue = self._manager.Queue()
        self._output_queue = self._manager.Queue()
        self._process_manager = ProcessManager(
            input_queue=self._input_queue,
            output_queue=self._output_queue,
            process_restart_period_sec=process_restart_period_sec,
        )
        self._process_manager.start()

        self._periodic_queue = self._manager.Queue()
        self._periodic_listener = PeriodicQueueListener(
            publish_method=self.publish_to_rabbit,
            periodic_queue=self._periodic_queue,
        )
        self._periodic_listener.start()

    def send_command(self, route: str):
        try:
            self._input_queue.put(
                CommandTransferObject(
                    callback=self._funcs[route],
                    args=[],
                    kwargs={'periodic_queue': self._periodic_queue},
                )
            )
        except KeyError as key_error:
            raise Exception(f"Invalid route {route}") from key_error

        return self._output_queue.get()

    def stop(self):
        self._connection.close()

        if self._process_manager.is_alive():
            self._process_manager.stop()
            self._process_manager.join()

        if self._periodic_listener.is_alive():
            self._periodic_listener.stop()
            self._periodic_listener.join()
