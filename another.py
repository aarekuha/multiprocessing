from random import randint
from queue import Queue as MultiprocessingQueue
from periodic_queue_listener import PeriodicTransferObject
# from decorators import Decorators


# @Decorators.action(route="first_route")
def custom_function(periodic_queue: MultiprocessingQueue) -> int:
    periodic_queue.put(PeriodicTransferObject(ttl=1, payload={'message': 'from process'}))
    return randint(0, 300) + 22
