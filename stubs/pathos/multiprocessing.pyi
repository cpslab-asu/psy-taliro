from typing import Callable, Sequence, TypeVar

_T = TypeVar("_T")
_U = TypeVar("_U")

class ProcessPool:
    def __init__(self, nodes: int): ...
    def map(self, f: Callable[[_T], _U], *args: Sequence[_T]) -> Sequence[_U]: ...
