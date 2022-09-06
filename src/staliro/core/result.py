from __future__ import annotations

import statistics as stats
from abc import abstractmethod
from typing import Any, Generic, Iterable, Optional, Protocol, Sequence, Tuple, TypeVar, cast

import numpy as np
from attr import frozen
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

from .interval import Interval
from .layout import SampleLayout
from .sample import Sample
from .signal import Signal

ResultT = TypeVar("ResultT")
ExtraT = TypeVar("ExtraT")
CostT = TypeVar("CostT")


class Comparable(Protocol):
    @abstractmethod
    def __eq__(self, other: Any) -> bool:
        pass

    @abstractmethod
    def __lt__(self: ComparableT, other: ComparableT) -> bool:
        pass


ComparableT = TypeVar("ComparableT", bound=Comparable)


@frozen()
class TimingData:
    """Storage class for execution durations of different PSY-TaLiRo components.

    The durations stored in this class are for a single evaluation.

    Attributes:
        model: Run time of model component
        specification: Run time of specification component
    """

    model: float
    specification: float

    @property
    def total(self) -> float:
        """The total duration of all components."""

        return self.model + self.specification


@frozen()
class Evaluation(Generic[CostT, ExtraT]):
    """The result of applying the cost function to a sample.

    Attributes:
        cost: The result of using a specification to analyze the output of a model
        sample: The sample provided to the model
        extra: Additional data returned by the model
        timing: Execution durations of each component of the cost function
    """

    cost: CostT
    sample: Sample
    extra: ExtraT
    timing: TimingData


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
class Run(Generic[ResultT, CostT, ExtraT]):
    """Data class that represents one run of an optimizer.

    Attributes:
        result: The value returned by the optimizer
        history: List of Evaluation instances representing every cost function evaluation
        duration: Time spent by the optimizer
    """

    result: ResultT
    history: Sequence[Evaluation[CostT, ExtraT]]
    duration: float
    seed: int

    @property
    def fastest_eval(self) -> Evaluation[CostT, ExtraT]:
        """The evaluation with the lowest total duration."""

        return min(self.history, key=lambda e: e.timing.total)

    @property
    def slowest_eval(self) -> Evaluation[CostT, ExtraT]:
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


def best_eval(run: Run[Any, ComparableT, ExtraT]) -> Evaluation[ComparableT, ExtraT]:
    return max(run.history, key=lambda e: e.cost)


def worst_eval(run: Run[Any, ComparableT, ExtraT]) -> Evaluation[ComparableT, ExtraT]:
    return min(run.history, key=lambda e: e.cost)


@frozen(slots=True)
class Result(Generic[ResultT, CostT, ExtraT]):
    """Data class that represents a set of successful runs of the optimizer.

    Attributes:
        runs: List of Run instances representing each optimization attempt
        options: Configuration class used to control Model, Specification and Optimizer behaviors
                 for each run
    """

    runs: Sequence[Run[ResultT, CostT, ExtraT]]
    interval: Interval
    seed: int
    processes: Optional[int]
    layout: SampleLayout

    def plot_signal(self, signal: Signal, step_size: float = 0.1) -> Tuple[Figure, Axes]:
        fig, ax = plt.subplots()
        times = np.arange(self.interval.lower, self.interval.upper, step_size, dtype=np.float64)
        values = signal.at_times(cast(Sequence[float], times.tolist()))

        ax.plot(times, values)

        return fig, ax


def best_run(result: Result[ResultT, ComparableT, ExtraT]) -> Run[ResultT, ComparableT, ExtraT]:
    return max(result.runs, key=best_eval)


def worst_run(result: Result[ResultT, ComparableT, ExtraT]) -> Run[ResultT, ComparableT, ExtraT]:
    return min(result.runs, key=worst_eval)
