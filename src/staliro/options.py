from __future__ import annotations

import enum
import os
import random
import sys
from typing import Any, List, Optional, Tuple, Union

if sys.version_info >= (3, 9):
    from collections.abc import Iterable, Sequence
else:
    from typing import Iterable, Sequence

from attr import attrs, attrib, Attribute
from attr.validators import optional
from typing_extensions import Literal

from .signals import InterpolatorFactory, PchipFactory


def _bounds_converter(value: Any) -> Any:
    if isinstance(value, Interval):
        return value.bounds

    return value


@attrs(auto_attribs=True)
class Interval:
    """Representation of an interval of values.

    Attributes:
        bounds: The upper and lower values of the interval
    """

    bounds: Sequence[float] = attrib(converter=_bounds_converter)

    @bounds.validator
    def _validate_values(self, attr: Attribute[Sequence[float]], value: Sequence[float]) -> None:
        if len(value) != 2:
            raise ValueError("only 2 values may be passed to interval")

        if value[0] > value[1]:
            raise ValueError("first value must be strictly less than second value")

    @property
    def lower(self) -> float:
        """The lower value of the interval."""

        return self.bounds[0]

    @property
    def upper(self) -> float:
        """The upper value of the interval."""
        return self.bounds[1]

    def astuple(self) -> Tuple[float, float]:
        """Representation of the interval as a tuple."""

        return (self.lower, self.upper)


SignalTimes = Sequence[float]


@attrs
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

    interval: Interval = attrib(converter=Interval)
    factory: InterpolatorFactory = attrib(factory=PchipFactory)
    control_points: int = attrib(default=10, converter=int)
    step: float = attrib(default=0.1, converter=float)
    signal_times: Optional[SignalTimes] = attrib(default=None)
    time_varying: bool = False  # Boolean flag for turning control point times into search variables

    @control_points.validator
    def _validate_control_points(self, attr: Attribute[int], value: int) -> None:
        if value < 0:
            raise ValueError("control points must be greater than zero")

    @step.validator
    def _validate_step(self, attr: Attribute[float], value: float) -> None:
        if value < 0:
            raise ValueError("step must be greater than zero")

    @factory.validator
    def _validate_factory(
        self, attr: Attribute[InterpolatorFactory], value: InterpolatorFactory
    ) -> None:
        if not isinstance(value, InterpolatorFactory):
            raise ValueError("factory must implement InterpolatorFactory protocol")

    @signal_times.validator
    def _validate_signal_times(
        self, attr: Attribute[Optional[SignalTimes]], value: Optional[SignalTimes]
    ) -> None:
        if value is not None and len(value) != self.control_points:
            raise ValueError("must specify as many signal times as control points")

    @property
    def bounds(self) -> List[Interval]:
        """The interval value repeated control_points number of times."""

        return [self.interval] * self.control_points


class Behavior(enum.IntEnum):
    """Behavior when falsifying case for system is encountered.

    Attributes:
        FALSIFICATION: Stop searching when the first falsifying case is encountered
        MINIMIZATION: Continue searching after encountering a falsifying case until iteration
                      budget is exhausted
    """

    FALSIFICATION = enum.auto()
    MINIMIZATION = enum.auto()


def _static_parameter_converter(obj: Any) -> List[Interval]:
    return [Interval(elem) for elem in obj]


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


@attrs
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

    static_parameters: List[Interval] = attrib(factory=list, converter=_static_parameter_converter)
    signals: Iterable[SignalOptions] = attrib(factory=list)
    seed: int = attrib(factory=_seed_factory)
    iterations: int = attrib(default=400, converter=int)
    runs: int = attrib(default=1, converter=int)
    interval: Interval = attrib(default=Interval([0, 1]), converter=Interval)
    behavior: Behavior = attrib(default=Behavior.FALSIFICATION)
    parallelization: _ParallelizationT = attrib(
        default=None, validator=optional(_parallelization_validator)
    )
    verbose: bool = False

    @runs.validator
    def _validate_runs(self, attr: Attribute[int], value: int) -> None:
        if value < 0:
            raise ValueError("runs must be greater than zero")

    @signals.validator
    def _validate_signals(
        self, attr: Attribute[List[SignalOptions]], signals: List[SignalOptions]
    ) -> None:
        for signal in signals:
            if not isinstance(signal, SignalOptions):
                raise ValueError("can only provide SignalOptions objects to signals attribute")

    @property
    def bounds(self) -> List[Interval]:
        """List of the static parameter bounds followed by the signal bounds."""

        signal_bounds = [bound for signal in self.signals for bound in signal.bounds]
        static_bounds = list(self.static_parameters)

        return static_bounds + signal_bounds

    @property
    def process_count(self) -> Optional[int]:
        """Number of processes to use based on the value of the parallelization attribute."""

        if self.parallelization == "all":
            return self.runs
        elif self.parallelization == "cores":
            return os.cpu_count()
        else:
            return self.parallelization
