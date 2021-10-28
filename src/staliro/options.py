from __future__ import annotations

import os
import random
import collections.abc as cabc
from typing import Any, List, Optional, Sequence, Tuple, Union, cast

import numpy as np
from attr import Attribute, field, frozen
from attr.validators import deep_iterable, instance_of
from attr.converters import optional
from numpy.typing import NDArray
from typing_extensions import Literal

from .core.interval import Interval
from .core.signal import SignalFactory
from .signals import Pchip


class OptionsError(Exception):
    pass


_IntervalValueT = Union[
    Interval,
    List[float],
    List[int],
    Tuple[float, float],
    Tuple[int, int],
    NDArray[np.float_],
    NDArray[np.int_],
]


def _strict_float(value: Union[int, float]) -> float:
    if isinstance(value, int):
        return float(value)

    if isinstance(value, float):
        return value

    raise OptionsError(f"Expected float or int, received {type(value)}")


def _strict_int(value: Union[int, float]) -> int:
    if isinstance(value, int):
        return value

    if isinstance(value, float):
        return int(value)

    raise OptionsError(f"Expected float or int, received {type(value)}")


def _to_interval(value: _IntervalValueT) -> Interval:
    """Convert a value to an interval.

    This function only supports ordered collections because the order of values in the iterable
    matters when trying to construct an interval. Iterables like Set do not guarantee the order of
    iteration, which can lead to non-deterministic failures.

    Arguments:
        value: The value to convert to an interval. Must be an Interval instance, list or tuple

    Returns:
        An instance of Interval using the values provided in the ordered collection
    """

    if isinstance(value, Interval):
        return value

    if isinstance(value, np.ndarray):
        return _to_interval(value.tolist())

    if isinstance(value, (list, tuple)):
        if len(value) != 2:
            raise OptionsError("Interval value must have length 2")

        return Interval(*value)

    raise TypeError(f"unsupported type {type(value)} provided as interval")


_SignalTimesValueT = Union[Sequence[float], Sequence[int], NDArray[Any]]
_SignalTimesT = List[float]


def _to_signal_times(values: _SignalTimesValueT) -> _SignalTimesT:
    if isinstance(values, np.ndarray):
        return cast(List[float], values.astype(np.float64).tolist())

    if isinstance(values, cabc.Sequence):
        return [_strict_float(value) for value in values]

    raise OptionsError(f"signal times must be provided as an ordered sequence. Got {type(values)}")


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

    bound: Interval = field(converter=_to_interval)
    factory: SignalFactory = field(default=Pchip)
    control_points: int = field(default=10, converter=_strict_int)
    signal_times: Optional[_SignalTimesT] = field(
        default=None, converter=optional(_to_signal_times)
    )
    time_varying: bool = field(default=False)

    @property
    def bounds(self) -> List[Interval]:
        """The interval value repeated control_points number of times."""

        return [self.bound] * self.control_points


_IntervalSeqT = Sequence[_IntervalValueT]


def _to_intervals(values: _IntervalSeqT) -> List[Interval]:
    if isinstance(values, cabc.Sequence):
        return [_to_interval(value) for value in values]

    raise OptionsError(f"Intervals must be provided as an ordered sequence. Got {type(values)}")


def _seed_factory() -> int:
    return random.randint(0, 2 ** 32 - 1)


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

    static_parameters: List[Interval] = field(factory=list, converter=_to_intervals)
    signals: Sequence[SignalOptions] = field(
        factory=list, validator=deep_iterable(instance_of(SignalOptions))
    )
    seed: int = field(factory=_seed_factory, converter=_strict_int)
    iterations: int = field(default=400, converter=_strict_int)
    runs: int = field(default=1, converter=_strict_int)
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
