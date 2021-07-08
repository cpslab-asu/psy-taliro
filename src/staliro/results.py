from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Generic, TypeVar

from .optimizers import Sample


@dataclass(frozen=True)
class Iteration:
    cost: float
    sample: Sample


@dataclass(frozen=True)
class TimedIteration(Iteration):
    model_duration: float
    cost_duration: float


_RT = TypeVar("_RT")
_IT = TypeVar("_IT", bound=Iteration)


@dataclass(frozen=True)
class Run(Generic[_RT, _IT]):
    result: _RT
    history: Sequence[_IT]
    duration: float

    @property
    def best_iter(self) -> _IT:
        return min(self.history, key=lambda i: i.cost)


@dataclass(frozen=True)
class StaliroResult(Generic[_RT, _IT]):
    runs: Sequence[Run[_RT, _IT]]
    seed: int

    @property
    def best_run(self) -> Run[_RT, _IT]:
        return min(self.runs, key=lambda r: r.best_iter.cost)
