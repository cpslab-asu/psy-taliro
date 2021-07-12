from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic, Sequence, Union

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from numpy import float_, int_
from numpy.typing import NDArray

from ..options import Interval, Behavior


@dataclass(frozen=True)
class OptimizationParams:
    bounds: Sequence[Interval]
    iterations: int
    behavior: Behavior
    seed: int


Sample = NDArray[Union[float_, int_]]


class OptimizationFn(Protocol):
    def __call__(self, __sample: Sample) -> float:
        ...


_T = TypeVar("_T")


class Optimizer(ABC, Generic[_T]):
    @abstractmethod
    def optimize(self, func: OptimizationFn, params: OptimizationParams) -> _T:
        raise NotImplementedError()
