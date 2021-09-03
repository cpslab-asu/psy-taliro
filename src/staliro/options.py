from __future__ import annotations

import os
import random
import sys
from typing import Any, Callable, Iterable, List, Literal, Optional, Sequence, Tuple, Union

import numpy as np
from attr import Attribute, field, frozen
from attr.validators import deep_iterable, instance_of, is_callable, optional
from numpy.typing import NDArray

from .core.interval import Interval
from .core.optimizer import Behavior as OptimizerBehavior
from .core.signal import Signal
from .signals import Pchip


def _greater_than(lower: float) -> Callable[[Any, Attribute[Any], float], None]:
    def _validator(_: Any, attr: Attribute[Any], value: float) -> None:
        if value <= lower:
            raise ValueError(f"{attr.name} must be strictly greater than {lower}")

    return _validator


IntervalValueT = Union[Interval, List[float], List[int], Tuple[float, float], Tuple[int, int]]


def _to_interval(value: IntervalValueT) -> Interval:
    if isinstance(value, Interval):
        return value
    elif isinstance(value, (list, tuple)):
        if len(value) != 2:
            raise ValueError("interval length must be equal to 2")

        return Interval(value[0], value[1])

    raise TypeError("unsupported type provided as interval")


SignalFactory = Callable[[Sequence[float], Sequence[float]], Signal]


def _int_to_float(value: Union[float, int]) -> float:
    return float(value) if type(value) is int else value


SignalTimesValueT = Union[Iterable[float], Iterable[int], NDArray[Any], None]
SignalTimesT = Optional[List[float]]


def _to_signal_times(values: SignalTimesValueT) -> Optional[List[float]]:
    if values is None:
        return None
    if isinstance(values, np.ndarray):
        values_list = values.tolist()
    else:
        values_list = list(values)

    return [_int_to_float(value) for value in values_list]


def _signal_times_validator(obj: Any, attr: Attribute[Any], signal_times: SignalTimesT) -> None:
    if signal_times is not None and any(type(time) is not float for time in signal_times):
        raise ValueError("signal times must be floats")


@frozen()
class SignalOptions:
    """Options for signal generation.

    Attributes:
        interval: The interval the signal should be generated for
        factory: Factory to produce interpolators for the signal
        control_points: The number of points the optimizer should generate for the signal
        step: The step size when evaluating the signal
        signal_times: Time values for the generated control points
        time_varying: Flag that indicates that the signal times should be considered a search
                      variable (EXPERIMENTAL)
    """

    interval: Interval = field(converter=_to_interval)
    factory: SignalFactory = field(default=Pchip, validator=is_callable())
    control_points: int = field(default=10, converter=int, validator=_greater_than(0))
    step: float = field(default=0.1, converter=float, validator=_greater_than(0))
    _signal_times: Optional[List[float]] = field(
        default=None, converter=_to_signal_times, validator=_signal_times_validator
    )
    time_varying: bool = False  # Boolean flag for turning control point times into search variables

    def __attrs_post_init__(self) -> None:
        if self.signal_times is not None and len(self.signal_times) != self.control_points:
            raise ValueError("signal_times must have control_points number of elements")

    @property
    def bounds(self) -> List[Interval]:
        """The interval value repeated control_points number of times."""

        return [self.interval] * self.control_points

    @property
    def signal_times(self) -> List[float]:
        """Return the time values for a"""

        if self._signal_times is not None:
            time_values = self.signal_times
        else:
            time_values_array = np.linspace(
                start=self.interval.lower,
                stop=self.interval.upper,
                num=self.control_points,
                dtype=np.float64,
            )
            time_values = time_values_array.tolist()

        return time_values


def _to_static_parameters(obj: Iterable[Any]) -> List[Interval]:
    if not isinstance(obj, Iterable):
        raise TypeError("static_parameters must be iterable")

    return [_to_interval(elem) for elem in obj]


def _seed_factory() -> int:
    return random.randint(0, sys.maxsize)


_ParallelizationT = Union[int, Literal["all", "cores"], None]


def _parallelization_validator(
    _: Any, attr: Attribute[_ParallelizationT], value: _ParallelizationT
) -> None:
    if isinstance(value, str) and value != "cores" and value != "all":
        raise ValueError()
    elif not isinstance(value, int):
        raise TypeError()


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
        behavior: The behavior of the system when a falsifying case is found
        parallelization: Number of processes to use to parallelize runs of the optimizer.
                         Acceptable values are: "cores" - all available cores, "all" - all runs,
                         integer - number of processes.
        verbose: Print additional data during execution
    """

    static_parameters: List[Interval] = field(factory=list, converter=_to_static_parameters)
    signals: Iterable[SignalOptions] = field(
        factory=list, validator=deep_iterable(instance_of(SignalOptions))
    )
    seed: int = field(factory=_seed_factory)
    iterations: int = field(default=400, converter=int)
    runs: int = field(default=1, converter=int, validator=_greater_than(0))
    interval: Interval = field(default=Interval(0.0, 1.0), converter=_to_interval)
    behavior: OptimizerBehavior = field(default=OptimizerBehavior.FALSIFICATION)
    parallelization: _ParallelizationT = field(
        default=None, validator=optional(_parallelization_validator)
    )
    verbose: bool = False

    @property
    def bounds(self) -> List[Interval]:
        """List of the static parameter bounds followed by the signal bounds."""

        return self.static_parameters + [bound for sig in self.signals for bound in sig.bounds]

    @property
    def process_count(self) -> Optional[int]:
        """Number of processes to use based on the value of the parallelization attribute."""

        if self.parallelization == "all":
            return self.runs
        elif self.parallelization == "cores":
            return os.cpu_count()
        else:
            return self.parallelization
