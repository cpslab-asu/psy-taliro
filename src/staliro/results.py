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
    """Data class that represents the standard statistics of a set of durations."""

    _durations: Iterable[float]

    @property
    def average_time(self) -> float:
        """The average of all durations."""

        return stats.mean(self._durations)

    @property
    def total_time(self) -> float:
        """The sum of all durations."""

        return sum(self._durations)

    @property
    def longest_duration(self) -> float:
        """The maximum duration."""

        return max(self._durations)


_RT = TypeVar("_RT")
_ET = TypeVar("_ET")


@dataclass(frozen=True)
class Run(Generic[_RT, _ET]):
    """Data class that represents one run of an optimizer.

    Attributes:
        result: The value returned by the optimizer
        history: List of Evaluation instances representing every cost function evaluation
        duration: Time spent by the optimizer
    """

    result: _RT
    history: Sequence[Evaluation[_ET]]
    duration: float

    @property
    def best_iter(self) -> Evaluation[_ET]:
        """The evaluation with the lowest cost (closest to falsification)."""

        return min(self.history, key=lambda i: i.cost)

    @property
    def fastest_iter(self) -> Evaluation[_ET]:
        """The evaluation with the lowest total duration."""

        return min(self.history, key=lambda i: i.timing.total)

    @property
    def model(self) -> TimeStats:
        """Time statistics for the model."""

        return TimeStats(iteration.timing.model for iteration in self.history)

    @property
    def specification(self) -> TimeStats:
        """Time statistics of the specification."""

        return TimeStats(iteration.timing.specification for iteration in self.history)


@dataclass(frozen=True)
class Result(Generic[_RT, _ET]):
    """Data class that represents a set of successful runs of the optimizer.

    Attributes:
        runs: List of Run instances representing each optimization attempt
        options: Configuration class used to control Model, Specification and Optimizer behaviors
                 for each run
    """

    runs: Sequence[Run[_RT, _ET]]
    options: Options

    @property
    def best_run(self) -> Run[_RT, _ET]:
        return min(self.runs, key=lambda r: r.best_iter.cost)
