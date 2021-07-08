from __future__ import annotations

from enum import auto, IntEnum
from random import randint
from sys import maxsize
from typing import Any, List, Optional, Tuple, Iterable, Sequence

from attr import attrs, attrib, Attribute

from .signals import InterpolatorFactory, PchipFactory


def _bounds_converter(value: Any) -> Any:
    if isinstance(value, Interval):
        return value.bounds

    return value


@attrs(auto_attribs=True)
class Interval:
    bounds: Sequence[float] = attrib(converter=_bounds_converter)

    @bounds.validator
    def _validate_values(self, attr: Attribute[Sequence[float]], value: Sequence[float]) -> None:
        if len(value) != 2:
            raise ValueError("only 2 values may be passed to interval")

        if value[0] > value[1]:
            raise ValueError("first value must be strictly less than second value")

    @property
    def lower(self) -> float:
        return self.bounds[0]

    @property
    def upper(self) -> float:
        return self.bounds[1]

    def astuple(self) -> Tuple[float, float]:
        return (self.lower, self.upper)


SignalTimes = Sequence[float]


@attrs
class SignalOptions:
    """Options for signal generation.

    Attributes:
        bound: The interval the signal should be generated for
        control_points: The number of points the optimizer should generate for the signal
        factory: Factory to produce interpolators for the signal
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
    time_varying: bool = (
        False  # Boolean flag for turning control point times into search variables
    )

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
        return [self.interval] * self.control_points


class Behavior(IntEnum):
    """Behavior when falsifying case for system is encountered.

    Attributes:
        FALSIFICATION: Stop searching when the first falsifying case is encountered
        MINIMIZATION: Continue searching after encountering a falsifying case until iteration
                      budget is exhausted
    """

    FALSIFICATION = auto()
    MINIMIZATION = auto()


def _static_parameter_converter(obj: Any) -> List[Interval]:
    return [Interval(elem) for elem in obj]


def _seed_factory() -> int:
    return randint(0, maxsize)


@attrs
class Options:
    """General options for controlling falsification behavior.

    Attributes:
        iterations: The number of search iterations to perform in a run
        runs: The number times to run the optimizer
        interval: The time interval of the system simulation
        behavior: The behavior of the system when a falsifying case is found
        static_parameters: Parameters that will be provided to the system at the beginning and are
                           time invariant (initial conditions)
        signals: System inputs that will vary over time
        verbose: Print additional data during execution
        bounds: The combined bounds from both the static_parameters and signals
    """

    static_parameters: List[Interval] = attrib(factory=list, converter=_static_parameter_converter)
    signals: Iterable[SignalOptions] = attrib(factory=list)
    seed: int = attrib(factory=_seed_factory)
    iterations: int = attrib(default=400, converter=int)
    runs: int = attrib(default=1, converter=int)
    interval: Interval = attrib(default=Interval([0, 1]), converter=Interval)
    sampling_interval: float = attrib(default=0.1, converter=float)
    behavior: Behavior = attrib(default=Behavior.FALSIFICATION)
    verbose: bool = False

    @runs.validator
    def _validate_runs(self, attr: Attribute[int], value: int) -> None:
        if value < 0:
            raise ValueError("runs must be greater than zero")

    @sampling_interval.validator
    def _validate_sampling_interval(self, attr: Attribute[float], value: float) -> None:
        if value < 0:
            raise ValueError("sampling interval must be greater than zero")

    @signals.validator
    def _validate_signals(
        self, attr: Attribute[List[SignalOptions]], signals: List[SignalOptions]
    ) -> None:
        for signal in signals:
            if not isinstance(signal, SignalOptions):
                raise ValueError("can only provide SignalOptions objects to signals attribute")

    @property
    def bounds(self) -> List[Interval]:
        signal_bounds = [bound for signal in self.signals for bound in signal.bounds]
        static_bounds = list(self.static_parameters)

        return static_bounds + signal_bounds
