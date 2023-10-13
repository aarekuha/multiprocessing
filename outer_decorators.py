from typing import Callable


class OuterDecorators:
    _funcs: dict[str, Callable] = {}
