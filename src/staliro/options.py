from __future__ import annotations

import os
import random
from typing import Any, List, Optional, Sequence, Tuple, Union, cast

import numpy as np
from attr import Attribute, converters, field, frozen, validators
from numpy.typing import NDArray
from typing_extensions import Literal

from .core.interval import BoundT, Interval
from .core.signal import SignalFactory
from .signals import pchip


class OptionsError(Exception):
    pass


_IntervalT = Union[Sequence[BoundT], NDArray[Any]]


def _to_interval(interval: Union[Interval, _IntervalT]) -> Interval:
    """Convert a value to an interval.

    This function only supports ordered collections because the order of values in the iterable
    matters when trying to construct an interval. Iterables like Set do not guarantee the order of
    iteration, which can lead to non-deterministic failures.

    Arguments:
        value: The value to convert to an interval. Must be an Interval instance, list or tuple

    Returns:
        An instance of Interval using the values provided in the ordered collection
    """

    if isinstance(interval, Interval):
        return interval

    if isinstance(interval, np.ndarray):
        interval = interval.astype(float)

    return Interval(interval[0], interval[1])


_IntervalsT = Sequence[_IntervalT]


def _to_intervals(intervals: _IntervalsT) -> Tuple[Interval, ...]:
    """Convert a sequence of values into a sequence on intervals."""

    return tuple(_to_interval(interval) for interval in intervals)


def _to_signal_times(times: Union[Sequence[float], NDArray[np.float_]]) -> list[float]:
    if isinstance(times, np.ndarray):
        return cast(List[float], np.array(times, dtype=float).tolist())

    return list(times)


@frozen()
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

    control_points: Tuple[Interval, ...] = field(converter=_to_intervals)
    factory: SignalFactory = field(default=pchip, validator=validators.is_callable())
    signal_times: Optional[list[float]] = field(
        default=None,
        converter=converters.optional(_to_signal_times),
        validator=validators.optional(
            validators.deep_iterable(validators.instance_of(float), validators.instance_of(list))
        ),
    )
    time_varying: bool = field(default=False)


def _seed_factory() -> int:
    return random.randint(0, 2**32 - 1)


_ParallelizationT = Union[None, Literal["all", "cores"], int]


def _parallelization_validator(_: Any, attr: Attribute[Any], value: _ParallelizationT) -> None:
    is_none = value is None
    is_valid_str = value in {"all", "cores"}
    is_int = isinstance(value, int)

    if not is_none and not is_valid_str and not is_int:
        raise OptionsError(
            "invalid parallelization value. Allowed types are: [None, 'all', 'cores', int]"
        )


@frozen()
class Options:
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

    static_parameters: Tuple[Interval, ...] = field(factory=tuple, converter=_to_intervals)
    signals: Sequence[SignalOptions] = field(
        factory=list, validator=validators.deep_iterable(validators.instance_of(SignalOptions))
    )
    seed: int = field(
        factory=_seed_factory, validator=[validators.instance_of(int), validators.gt(0)]
    )
    iterations: int = field(default=400, validator=[validators.instance_of(int), validators.gt(0)])
    runs: int = field(default=1, validator=[validators.instance_of(int), validators.gt(0)])
    interval: Interval = field(default=Interval(0.0, 10.0), converter=_to_interval)
    parallelization: _ParallelizationT = field(default=None, validator=_parallelization_validator)

    @property
    def process_count(self) -> Optional[int]:
        """Number of processes to use based on the value of the parallelization attribute."""

        if self.parallelization == "all":
            return self.runs
        elif self.parallelization == "cores":
            return os.cpu_count()
        else:
            return self.parallelization
