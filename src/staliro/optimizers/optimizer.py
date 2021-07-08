from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, TypeVar, Generic, Sequence, Union

from numpy import float_, int_
from numpy.typing import NDArray

from ..options import Interval, Behavior


@dataclass
class RunOptions:
    bounds: Sequence[Interval]
    iterations: int
    behavior: Behavior
    seed: int


Sample = NDArray[Union[float_, int_]]
ObjectiveFn = Callable[[Sample], float]
_T = TypeVar("_T")


class Optimizer(ABC, Generic[_T]):
    @abstractmethod
    def optimize(self, func: ObjectiveFn, options: RunOptions) -> _T:
        raise NotImplementedError()
