from __future__ import annotations

import statistics as stats
from typing import Generic, Iterable, Optional, Sequence, TypeVar

from attr import frozen

from .cost import Evaluation
from .interval import Interval

RT = TypeVar("RT")
ET = TypeVar("ET")


@frozen(slots=True)
class TimeStats:
    """Data class that represents the standard statistics of a set of durations."""

    durations: Iterable[float]

    @property
    def total_duration(self) -> float:
        """The sum of all durations."""

        return sum(self.durations)

    @property
    def avg_duration(self) -> float:
        """The average of all durations."""

        return stats.mean(self.durations)

    @property
    def max_duration(self) -> float:
        """The maximum duration."""

        return max(self.durations)

    @property
    def min_duration(self) -> float:
        """The maximum duration."""

        return min(self.durations)


@frozen(slots=True)
class Run(Generic[RT, ET]):
    """Data class that represents one run of an optimizer.

    Attributes:
        result: The value returned by the optimizer
        history: List of Evaluation instances representing every cost function evaluation
        duration: Time spent by the optimizer
    """

    result: RT
    history: Sequence[Evaluation[ET]]
    duration: float
    seed: int

    @property
    def worst_eval(self) -> Evaluation[ET]:
        """The evaluation with the highest cost (furthest from falsifying)."""

        return max(self.history, key=lambda e: e.cost)

    @property
    def best_eval(self) -> Evaluation[ET]:
        """The evaluation with the lowest cost (closest to falsification)."""

        return min(self.history, key=lambda e: e.cost)

    @property
    def fastest_eval(self) -> Evaluation[ET]:
        """The evaluation with the lowest total duration."""

        return min(self.history, key=lambda e: e.timing.total)

    @property
    def slowest_eval(self) -> Evaluation[ET]:
        """Evaluation with the longest total duration."""

        return max(self.history, key=lambda e: e.timing.total)

    @property
    def model_timing(self) -> TimeStats:
        """Time statistics for the model."""

        return TimeStats(iteration.timing.model for iteration in self.history)

    @property
    def specification_timing(self) -> TimeStats:
        """Time statistics of the specification."""

        return TimeStats(iteration.timing.specification for iteration in self.history)


@frozen(slots=True)
class Result(Generic[RT, ET]):
    """Data class that represents a set of successful runs of the optimizer.

    Attributes:
        runs: List of Run instances representing each optimization attempt
        options: Configuration class used to control Model, Specification and Optimizer behaviors
                 for each run
    """

    runs: Sequence[Run[RT, ET]]
    interval: Interval
    seed: int
    processes: Optional[int]

    @property
    def worst_run(self) -> Run[RT, ET]:
        return max(self.runs, key=lambda r: r.worst_eval.cost)

    @property
    def best_run(self) -> Run[RT, ET]:
        return min(self.runs, key=lambda r: r.best_eval.cost)
