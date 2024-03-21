"""
Definition of the interface for the continuous, time-varying functions called signals.

A signal is contunious, time-varying input to a system that can represent anything from control
inputs from a user to environmental effects. The `Signal` class captures this behavior, and is
constructed from a set of times and a set of values called *control points*. Each control point
is associated with a time and represents the value of the signal at that particular time.

Users configure the signal inputs to their system by providing a dictionary of `SignalInput`
values where the key for each value is the name of the signal. To customize the behavior of the
generated input signal, the ``factory`` argument can be used when constructing a ``SignalInput``
which accepts a `SignalFactory` function.

Implementations
---------------

This module provides some ready to use ``Signal`` implementations, as well as a few combinator
functions to further customize the behavior of the signals. The basic signal implementations are:

- `pchip`
- `piecewise_linear`
- `piecewise_constant`
- `harmonic`

A signal combinator is a function that takes a signal factory as input and returns a signal factory
as output. The primary use of these functions is to modify the behavior of existing signals without
needing to implement one for each signal you wish to modify. The combinators provided by this
library are:

- `delayed`
- `sequenced`
- `clamped`

Examples
--------

.. code-block:: python

    from staliro import TestOptions, signals

    class Constant(signals.Signal):
        def __init__(self, value: float):
            self.value = value

        def at_time(self, time: float) -> float:
            return self.value


    def constant(times: Iterable[float], control_points: Iterable[float]) -> Constant:
        return Constant(control_points[0])


    options = TestOptions(
        tspan=(0, 10),
        signals={
            "const": SignalInput(
                control_points=[(0, 10)],
                factory=constant,
            ),
            "delayed": SignalInput(
                control_points=[(0, 10), (10, 20)],
                factory=signals.delayed(signals.pchip, delay=5.0)
            ),
            "sequenced": SignalInput(
                control_points=[(0, 10), (0, 10)],,
                factory=signals.sequenced(signals.piecewise_linear, signals.piecewise_constant)
            ),
            "harmonic": SignalInput(
                control_points=[(0, 10), (0, 1.0), (3.0, 5.0), (0, 3.14)],
                factory=signals.harmonic,
            )
        },
    )

"""

from __future__ import annotations

import math
import warnings
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from math import cos
from typing import Protocol, SupportsFloat, Union, cast

import numpy as np
from attrs import Attribute, define, field, frozen, validators
from numpy.typing import NDArray
from scipy.interpolate import PchipInterpolator, interp1d
from typing_extensions import TypeAlias


class Signal(ABC):
    """Representation of a time-varying input to a system."""

    @abstractmethod
    def at_time(self, time: float) -> float:
        """Get the value of the signal at the specified time."""

        raise NotImplementedError()

    def at_times(self, times: Sequence[float]) -> list[float]:
        """Get the value of the signal at each specified time."""

        return [self.at_time(time) for time in times]


class SignalFactory(Protocol):
    """Factory interface for creating signals from a set of times and control points."""

    def __call__(self, __times: Iterable[float], __control_points: Iterable[float]) -> Signal:
        """Create a `Signal` from a set of times and control points.

        The number of times and control points can be assumed to be equal.

        :param times: The time value for each control point
        :param control_points: The values of the signal at the given times
        :returns: A signal
        """


class Pchip(Signal):
    """Signal using PChip interpolation."""

    def __init__(self, interp: PchipInterpolator):
        self.interp = interp

    def at_time(self, t: float) -> float:
        return float(self.interp(t))

    def at_times(self, ts: Sequence[float]) -> list[float]:
        return cast(list[float], self.interp(ts).tolist())


def pchip(times: Iterable[float], control_points: Iterable[float]) -> Pchip:
    """Create a signal using PChip interpolation.

    Pchip is a smooth 3rd-order cubic spline interpolation.

    :param times: The time value for each control point
    :param control_points: The values of the signal at the given times
    :returns: A signal interpolated using PChip
    """

    return Pchip(PchipInterpolator(list(times), list(control_points)))


class Piecewise(Signal):
    """Signal using multiple piecewise functions."""

    def __init__(self, interp: interp1d):
        self.interp = interp

    def at_time(self, t: float) -> float:
        return float(self.interp(t))

    def at_times(self, ts: Sequence[float]) -> list[float]:
        return cast(list[float], self.interp(ts).tolist())


def piecewise_linear(times: Iterable[float], control_points: Iterable[float]) -> Piecewise:
    """Create a signal that is interpolated linearly between control points.

    The values of the signal between control points are interpolated by using the control point
    before and after the time to create a linear equation that is evaluated at the current time.

    :param times: The time values for each control point
    :param control_points: The values of the signal at the given times
    :returns: A piecewise linear interpolated signal
    """

    return Piecewise(interp1d(list(times), list(control_points)))


def piecewise_constant(times: Iterable[float], values: Iterable[float]) -> Piecewise:
    """Create a signal that is constant between control points.

    The values of the signal between control points are constant until the next control point.

    :param times: The time values for each control point
    :param control_points: The values of the signal at the given times
    :returns: A piecewise constant interpolated signal
    """

    return Piecewise(interp1d(list(times), list(values), kind="zero", fill_value="extrapolate"))


@define(slots=True)
class Delayed(Signal):
    """Signal with output of 0.0 before cutoff time."""

    signal: Signal
    cutoff: float

    def at_time(self, t: float) -> float:
        if t < self.cutoff:
            return 0.0

        return self.signal.at_time(t)


@frozen(slots=True)
class DelayedFactory(SignalFactory):
    inner: SignalFactory
    delay: float

    def __call__(self, times: Iterable[float], control_points: Iterable[float]) -> Delayed:
        values = list(control_points)
        stop_time = max(times)
        new_times = np.linspace(start=self.delay, stop=stop_time, num=len(values), dtype=float)
        signal = self.inner(new_times.tolist(), values)

        return Delayed(signal, self.delay)


def delayed(inner: SignalFactory, *, delay: float) -> SignalFactory:
    """Delay the control points inner signal by the given amount.

    :param inner: Factory for the signal to delay
    :param delay: The amount of time to delay
    :returns: A `SignalFactory` for the delayed signal
    """

    return DelayedFactory(inner, delay)


@define(slots=True)
class Sequenced(Signal):
    """Signal with output from s1 or s2 depending on evaluation time."""

    s1: Signal
    s2: Signal
    t_switch: float

    def at_time(self, t: float) -> float:
        return self.s1.at_time(t) if t < self.t_switch else self.s2.at_time(t)


@frozen(slots=True)
class SequencedFactory(SignalFactory):
    first: SignalFactory
    second: SignalFactory
    t_switch: float

    def __call__(self, times: Iterable[float], control_points: Iterable[float]) -> Signal:
        times_pts = zip(times, control_points)
        s1_data = [(time, value) for time, value in times_pts if time < self.t_switch]
        s1 = self.first((time for time, _ in s1_data), (value for _, value in s1_data))

        s2_data = [(time, value) for time, value in times_pts if time >= self.t_switch]
        s2 = self.second((time for time, _ in s2_data), (value for _, value in s2_data))

        return Sequenced(s1, s2, self.t_switch)


def sequenced(first: SignalFactory, second: SignalFactory, *, t_switch: float) -> SignalFactory:
    """Create a signal that will switch behavior at a given time.

    :param first: Factory for the signal to use before the switch time
    :param second: Factory for the signal to use after the switch time
    :param t_switch: The time to switch from first to second
    :returns: A `SignalFactory` for the sequenced signal
    """

    return SequencedFactory(first, second, t_switch)


class Harmonic(Signal):
    """Signal with output of the sum of multiple sinusoidal components."""

    class Component:
        def __init__(self, amplitude: float, frequency: float, phase: float):
            self.theta = amplitude
            self.omega = frequency
            self.phi = phase

        def at_time(self, time: float) -> float:
            return self.theta * cos(self.omega * time - self.phi)

    def __init__(self, bias: float, components: Sequence[Harmonic.Component]):
        self.bias = bias
        self.components = tuple(components)

    def at_time(self, time: float) -> float:
        return self.bias + sum(component.at_time(time) for component in self.components)


def harmonic(_: Iterable[float], control_points: Iterable[float]) -> Harmonic:
    """Create a signal that is the sum of multiple sinusoidal components.

    The bias value for this signal is the first control point and any harmonic components must be
    defined after the bias in groups of 3 with the order being the amplitude, frequency, and phase.

    :param times: Ignored
    :param control_points: The bias term, and the parameters for each harmonic component
    :returns: A signal composed of harmonic components
    """

    control_points = list(control_points)

    if len(control_points[1:]) % 3 != 0:
        raise RuntimeError("Insufficient number of values to generate a harmonic signal")

    bias = control_points[0]
    component_params = [
        (control_points[i], control_points[i + 1], control_points[i + 2])
        for i in range(1, len(control_points), 3)
    ]
    components = [Harmonic.Component(amp, freq, phase) for amp, freq, phase in component_params]

    return Harmonic(bias, components)


@define(slots=True)
class Clamped(Signal):
    """Signal with an output clamped between lo and hi."""

    signal: Signal
    lo: float
    hi: float

    def at_time(self, time: float) -> float:
        return min(self.hi, max(self.lo, self.signal.at_time(time)))


@frozen(slots=True)
class ClampedFactory(SignalFactory):
    inner: SignalFactory
    lo: float | None
    hi: float | None

    def __call__(self, times: Iterable[float], control_points: Iterable[float]) -> Signal:
        signal = self.inner(times, control_points)
        lo = self.lo or -math.inf
        hi = self.hi or math.inf

        return Clamped(signal, lo, hi)


def clamped(
    inner: SignalFactory, *, lo: float | None = None, hi: float | None = None
) -> SignalFactory:
    """Create a signal that will not exceed the given range.

    :param inner: Factory for the signal to clamp
    :param lo: The optional lower bound of the signal
    :param hi: The optional upper bound of the signal
    :returns: A `SignalFactory` for the clamped signal
    """

    return ClampedFactory(inner, lo, hi)


IntervalLike: TypeAlias = Union[Sequence[SupportsFloat], NDArray[np.float_]]
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
        interval = interval.astype(dtype=float)

    if len(interval) > 2:
        warnings.warn("Interval endpoints past 2 will be ignored.", stacklevel=2)

    return float(interval[0]), float(interval[1])


ControlPointsLike: TypeAlias = Union[Mapping[SupportsFloat, IntervalLike], Sequence[IntervalLike]]
ControlPoints: TypeAlias = Union[list[Interval], dict[float, Interval]]


def _to_control_points(pts: ControlPointsLike) -> ControlPoints:
    if isinstance(pts, Mapping):
        return {float(time): _to_interval(interval) for time, interval in pts.items()}

    return [_to_interval(interval) for interval in pts]


def _iter_pts(pts: list[Interval] | dict[float, Interval]) -> Iterable[Interval]:
    if isinstance(pts, dict):
        return pts.values()

    return pts


@define(kw_only=True)
class SignalInput:
    """Options for signal generation.

    :param control_points: The valid interval for each control point the optimizer should generate
                           for the signal
    :param factory: Function to create a signal from the generated times and control points
    :param time_varying: Flag that indicates that the signal times should be considered a search
                         variable (EXPERIMENTAL)
    """

    control_points: list[Interval] | dict[float, Interval] = field(
        converter=_to_control_points,
        validator=validators.min_len(1),
    )

    factory: SignalFactory = field(
        default=pchip,
        validator=validators.is_callable(),
    )

    time_varying: bool = field(default=False)

    @control_points.validator
    def _control_pts(self, _: Attribute[object], pts: ControlPoints) -> None:
        if len(pts) < 1:
            raise ValueError("Must provide at least 1 control point to signal")

        for pt in _iter_pts(pts):
            if pt[0] >= pt[1]:
                raise ValueError("Interval lower bound must be less than upper bound.")


__all__ = [
    "Signal",
    "SignalFactory",
    "SignalInput",
    "clamped",
    "delayed",
    "harmonic",
    "pchip",
    "piecewise_constant",
    "piecewise_linear",
    "sequenced",
]
