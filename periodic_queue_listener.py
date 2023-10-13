from typing import Callable, Dict, Optional
from threading import Thread
from dataclasses import dataclass
from contextlib import suppress
from queue import Queue as MultiprocessingQueue, Empty


@dataclass
class PeriodicTransferObject:
    ttl: int
    payload: Optional[Dict] = None
    reject_publish: bool = False


class PeriodicQueueListener(Thread):
    """Проброс сообщений в RabbitMQ из внутренней очереди
    Args:
        publish_method: метод, в который будет пробрасываться полученное сообщение
        periodic_queue: внутренняя очередь, из которой ожидаются сообщения для RabbitMQ
    """
    def __init__(self, publish_method: Callable[[PeriodicTransferObject], None], periodic_queue: MultiprocessingQueue):
        super().__init__()
        self._publish_method = publish_method
        self._periodic_queue = periodic_queue

    def run(self):
        self._stop_event = False
        while not self._stop_event:
            with suppress(Empty):
                self._publish_method(self._periodic_queue.get(timeout=1))

    def stop(self):
        self._stop_event = True
