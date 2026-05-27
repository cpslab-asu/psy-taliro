from collections.abc import Callable, Iterable
from typing import TypeVar

_T = TypeVar("_T")
_R = TypeVar("_R")

class AbstractWorkerPool:
    def map(self, func: Callable[[_T], _R], *args: Iterable[_T]) -> Iterable[_R]: ...
