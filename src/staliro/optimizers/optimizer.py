from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TypeVar, Generic, Sequence, Any

from ..cost import CostFn
from ..options import Interval, Behavior

OptimizationFn = CostFn[Any]


@dataclass(frozen=True)
class OptimizationParams:
    bounds: Sequence[Interval]
    iterations: int
    behavior: Behavior
    seed: int


_T = TypeVar("_T")


class Optimizer(ABC, Generic[_T]):
    @abstractmethod
    def optimize(self, func: OptimizationFn, params: OptimizationParams) -> _T:
        raise NotImplementedError()
