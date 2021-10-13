from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Protocol, Sequence, TypeVar

from attr import frozen

from .interval import Interval
from .sample import Sample

T = TypeVar("T")


class ObjectiveFn(Protocol):
    def eval_sample(self, sample: Sample) -> float:
        ...

    def eval_samples(self, samples: Sequence[Sample]) -> Sequence[float]:
        ...

    def eval_samples_parallel(self, samples: Sequence[Sample], processes: int) -> Sequence[float]:
        ...


@frozen(slots=True)
class OptimizationParams:
    bounds: Sequence[Interval]
    iterations: int
    behavior: Behavior
    seed: int


class Optimizer(Generic[T], ABC):
    @abstractmethod
    def optimize(self, func: ObjectiveFn, params: OptimizationParams) -> T:
        ...
