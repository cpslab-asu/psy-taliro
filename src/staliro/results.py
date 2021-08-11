from __future__ import annotations

import statistics as stats
import sys
from dataclasses import dataclass
from typing import Generic, TypeVar

if sys.version_info >= (3, 9):
    from collections.abc import Iterable, Sequence
else:
    from typing import Iterable, Sequence

from .cost import Evaluation
from .options import Options


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


_RT = TypeVar("_RT")
_ET = TypeVar("_ET")


@dataclass(frozen=True)
class Run(Generic[_RT, _ET]):
    result: _RT
    history: Sequence[Evaluation[_ET]]
    duration: float

    @property
    def best_iter(self) -> Evaluation[_ET]:
        return min(self.history, key=lambda i: i.cost)

    @property
    def fastest_iter(self) -> Evaluation[_ET]:
        return min(self.history, key=lambda i: i.timing.total)

    @property
    def model(self) -> TimeStats:
        return TimeStats(iteration.timing.model for iteration in self.history)

    @property
    def specification(self) -> TimeStats:
        return TimeStats(iteration.timing.specification for iteration in self.history)


@dataclass(frozen=True)
class Result(Generic[_RT, _ET]):
    runs: Sequence[Run[_RT, _ET]]
    options: Options

    @property
    def best_run(self) -> Run[_RT, _ET]:
        return min(self.runs, key=lambda r: r.best_iter.cost)
