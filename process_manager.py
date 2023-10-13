import time
import logging
from typing import (
    Callable,
    Any,
)
from multiprocessing import Process
from queue import Queue as MultiprocessingQueue, Empty as EmptyQueue

from contextlib import suppress
from threading import Thread
from dataclasses import dataclass


class ExitCommand:
    """Команда на останов потока после завершения обработки текущим процессом"""


@dataclass
class CommandTransferObject:
    """Объект передачи вызова в созданный процесс"""
    callback: Callable  # Вызываемая функция/метод
    args: list[Any]  # Аргументы функции/метода
    kwargs: dict[str, Any]  # Именованные аргументы функции/метода


class ProcessManager(Thread):
    """
    Поток управления процессом
    - осуществляюет переодический перезапуск процесса, в который заворачиваются ACT callback'и
    - транслирует сообщения из input_queue в целевую функцию/метод
        - сообщения содержат аргументы и именованые аргументы
    """
    _stop_event: bool
    _current_process: Process
    _process_life_time_sec: int

    def __init__(self,
        input_queue: MultiprocessingQueue,
        output_queue: MultiprocessingQueue,
        process_restart_period_sec: int,
    ) -> None:
        logging.error('ProcessManager initializing...')
        super().__init__()
        self._input_queue = input_queue
        self._output_queue = output_queue
        self._process_life_time_sec = process_restart_period_sec

    def _command_message_processor(
        self,
        input_queue: MultiprocessingQueue,
        output_queue: MultiprocessingQueue,
    ) -> None:
        """Транслирование аргументов и именованных аргументов в целевую функцию/метод"""
        has_exit_command: bool = False
        while not has_exit_command:
            with suppress(EmptyQueue):  # type: ignore[attr-defined]
                input_args = input_queue.get(timeout=1)
                if isinstance(input_args, ExitCommand):
                    has_exit_command = True
                    continue
                elif isinstance(input_args, CommandTransferObject):
                    cto = input_args
                    output_queue.put(cto.callback(*cto.args, **cto.kwargs))
                else:
                    logging.error(f"Invalid input command message: {input_args=}")

    def run(self) -> None:
        logging.error('ProcessManager starting...')
        ONE_TICK_SEC = 1  # Период проверок состояния
        total_seconds: int = self._process_life_time_sec  # Общее время жизни процесса
        total_repeats: float = total_seconds / ONE_TICK_SEC
        self._stop_event = False
        while not self._stop_event:
            logging.error('Started new processor')
            process = Process(
                target=self._command_message_processor,
                kwargs={
                    'input_queue': self._input_queue,
                    'output_queue': self._output_queue,
                },
            )
            process.start()
            for _ in range(int(total_repeats)):
                if self._stop_event:
                    break
                time.sleep(ONE_TICK_SEC)
            self._input_queue.put(ExitCommand())  # Команда на останов дочернего процесса
            process.join()

    def stop(self):
        self._stop_event = True
