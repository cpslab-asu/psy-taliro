from __future__ import annotations

import os
import random
from collections.abc import Sequence
from typing import Any, Literal, Union, cast

import numpy as np
from attr import Attribute, converters, define, field, validators
from numpy.typing import NDArray
from typing_extensions import TypeAlias

from .signals import SignalFactory, pchip

IntervalLike: TypeAlias = Union[Sequence[float], NDArray[Any]]
Interval: TypeAlias = tuple[float, float]


def _to_interval(interval: IntervalLike) -> Interval:
    """Convert a value to an interval.

    This function only supports ordered collections because the order of values in the iterable
    matters when trying to construct an interval. Iterables like Set do not guarantee the order of
    iteration, which can lead to non-deterministic failures.

    Arguments:
        value: The value to convert to an interval. Must be an Interval instance, list or tuple

    Returns:
        An instance of Interval using the values provided in the ordered collection
    """

    if isinstance(interval, np.ndarray):
        if interval.ndim != 1:
            raise ValueError("Only 1 dimensional arrays can be used as intervals")

        if interval.size != 2:
            raise ValueError("Only 2 value arrays can be used as intervals")

        interval = interval.astype(dtype=float)

    lower = interval[0]
    upper = interval[1]

    if lower >= upper:
        raise ValueError("Lower endpoint is >= upper endpoint")

    return lower, upper


def _to_intervals(intervals: Sequence[IntervalLike] | NDArray[np.float_]) -> list[Interval]:
    """Convert a sequence of values into a sequence on intervals."""

    if isinstance(intervals, np.ndarray):
        pass

    return [_to_interval(interval) for interval in intervals]


def _to_signal_times(times: Sequence[float] | NDArray[np.float_]) -> list[float]:
    if isinstance(times, np.ndarray):
        return cast(list[float], times.astype(dtype=float).tolist())

    signal_times = []

    for time in times:
        if not isinstance(time, float):
            raise TypeError(f"Signal times must be floating point values, found {type(time)}")

        signal_times.append(time)

    return signal_times


def _seed_factory() -> int:
    return random.randint(0, 2**32 - 1)


def _parallelization(_: Any, attr: Attribute[Any], value: Literal["all", "cores"] | int | None) -> None:
    if value is None:
        return

    if isinstance(value, int) and value < 1:
            raise ValueError("Parallelization must be <= 1")

    if isinstance(value, str) and value != "all" and value != "cores":
            raise ValueError("Only 'all' and 'cores' are supported parallelization options")

    raise TypeError(f"Unsupported type {type(value)} for parallelization.")


def _to_static_parameters(params: dict[str, IntervalLike]) -> dict[str, Interval]:
    converted = {}

    for name, interval in params.items():
        if not isinstance(name, str):
            raise TypeError("Only string keys supported in static parameters")

        converted[name] = _to_interval(interval)

    return converted


def _signals(_: Any, attr: Attribute[Any], signals: dict[str, SignalOptions]) -> None:
    for name, signal in signals.items():
        if not isinstance(name, str):
            raise TypeError("Only string keys supported in signals")

        if not isinstance(signal, SignalOptions):
            raise TypeError("Signals must be values of type Options.Signal")


@define()
class SignalOptions:
    """Options for signal generation.

    Attributes:
        interval: The interval the signal should be generated for
        factory: Factory to produce interpolators for the signal
        control_points: The number of points the optimizer should generate for the signal
        signal_times: Time values for the generated control points
        time_varying: Flag that indicates that the signal times should be considered a search
                      variable (EXPERIMENTAL)
    """

    control_points: list[Interval] = field(converter=_to_intervals)

    factory: SignalFactory = field(
        default=pchip,
        validator=validators.is_callable(),
    )

    signal_times: list[float] | None = field(
        default=None,
        converter=converters.optional(_to_signal_times),
    )

    time_varying: bool = field(default=False)


@define()
class TestOptions:
    """General options for controlling falsification behavior.

    Attributes:
        static_parameters: Parameters that will be provided to the system at the beginning and are
            time invariant (initial conditions)
        signals: System inputs that will vary over time
        seed: The initial seed of the random number generator
        iterations: The number of search iterations to perform in a run
        runs: The number times to run the optimizer
        interval: The time interval of the system simulation
        parallelization: Number of processes to use to parallelize runs of the optimizer. Acceptable
            values are: "cores" (all available cores), "all" (all runs), int (number of processes),
            None (no parallelization).
    """

    static_parameters: dict[str, Interval] = field(
        factory=dict,
        converter=_to_static_parameters,
    )

    signals: dict[str, SignalOptions] = field(
        factory=dict,
        validator=_signals,
    )

    seed: int = field(
        factory=_seed_factory,
        validator=[validators.instance_of(int), validators.gt(0)],
    )

    iterations: int = field(
        default=400,
        validator=[validators.instance_of(int), validators.gt(0)],
    )

    runs: int = field(
        default=1,
        validator=[validators.instance_of(int), validators.gt(0)]
    )

    tspan: Interval = field(
        default=(0.0, 1.0),
        converter=_to_interval,
    )

    parallelization: Literal["all", "cores"] | int | None = field(
        default=None,
        validator=_parallelization,
    )

    @property
    def processes(self) -> int | None:
        if self.parallelization == "all":
            return self.runs

        if self.parallelization == "cores":
            return os.cpu_count()

        return self.parallelization

    @property
    def layout(self) -> object:
        pass

