from __future__ import annotations

import statistics as stats
import sys
from dataclasses import dataclass
from typing import Generic, TypeVar

if sys.version_info >= (3, 9):
    from collections.abc import Iterable, Sequence
else:
    from typing import Iterable, Sequence

from .optimizers import Sample
from .options import Options

_ET = TypeVar("_ET")


@dataclass(frozen=True)
class Iteration(Generic[_ET]):
    cost: float
    sample: Sample
    extra: _ET


@dataclass(frozen=True)
class TimedIteration(Iteration[_ET]):
    model_duration: float
    cost_duration: float


_RT = TypeVar("_RT")


@dataclass(frozen=True)
class Run(Generic[_RT, _ET]):
    result: _RT
    history: Sequence[Iteration[_ET]]
    duration: float

    @property
    def best_iter(self) -> Iteration[_ET]:
        return min(self.history, key=lambda i: i.cost)


@dataclass(frozen=True)
class TimeStats:
    _durations: Iterable[float]

    @property
    def average_time(self) -> float:
        return stats.mean(self._durations)

    @property
    def total_time(self) -> float:
        return sum(self._durations)

    @property
    def longest_duration(self) -> float:
        return max(self._durations)


@dataclass(frozen=True)
class TimedRun(Run[_RT, _ET]):
    history: Sequence[TimedIteration[_ET]]

    @property
    def best_iter(self) -> TimedIteration[_ET]:
        return min(self.history, key=lambda i: i.cost)

    @property
    def fastest_iter(self) -> TimedIteration[_ET]:
        return min(self.history, key=lambda i: i.model_duration + i.cost_duration)

    @property
    def model(self) -> TimeStats:
        return TimeStats(iteration.model_duration for iteration in self.history)

    @property
    def cost_fn(self) -> TimeStats:
        return TimeStats(iteration.cost_duration for iteration in self.history)


@dataclass(frozen=True)
class Result(Generic[_RT, _ET]):
    runs: Sequence[Run[_RT, _ET]]
    options: Options

    @property
    def best_run(self) -> Run[_RT, _ET]:
        return min(self.runs, key=lambda r: r.best_iter.cost)


@dataclass(frozen=True)
class TimedResult(Result[_RT, _ET]):
    runs: Sequence[TimedRun[_RT, _ET]]

    @property
    def best_run(self) -> TimedRun[_RT, _ET]:
        return min(self.runs, key=lambda r: r.best_iter.cost)
