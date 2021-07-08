from __future__ import annotations

import sys
from dataclasses import dataclass
from statistics import mean
from typing import Generic, TypeVar

if sys.version_info >= (3, 9):
    from collections.abc import Iterable, Sequence
else:
    from typing import Iterable, Sequence

from .optimizers import Sample
from .options import Options


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


_TIT = TypeVar("_TIT", bound=TimedIteration)


@dataclass(frozen=True)
class TimeStats:
    _durations: Iterable[float]

    @property
    def average_time(self) -> float:
        return mean(self._durations)

    @property
    def total_time(self) -> float:
        return sum(self._durations)

    @property
    def longest_duration(self) -> float:
        return max(self._durations)


@dataclass(frozen=True)
class TimedRun(Run[_RT, _TIT]):
    @property
    def model(self) -> TimeStats:
        return TimeStats(iteration.model_duration for iteration in self.history)

    @property
    def cost_fn(self) -> TimeStats:
        return TimeStats(iteration.cost_duration for iteration in self.history)


@dataclass(frozen=True)
class Result(Generic[_RT, _IT]):
    runs: Sequence[Run[_RT, _IT]]
    options: Options

    @property
    def best_run(self) -> Run[_RT, _IT]:
        return min(self.runs, key=lambda r: r.best_iter.cost)


@dataclass(frozen=True)
class TimedResult(Result[_RT, _TIT]):
    runs: Sequence[TimedRun[_RT, _TIT]]

    @property
    def best_run(self) -> TimedRun[_RT, _TIT]:
        return min(self.runs, key=lambda r: r.best_iter.cost)
