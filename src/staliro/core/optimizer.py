from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, Protocol, Sequence, TypeVar

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


class Optimizer(Generic[T], ABC):
    @abstractmethod
    def optimize(self, func: ObjectiveFn, bounds: Sequence[Interval], budget: int, seed: int) -> T:
        ...
