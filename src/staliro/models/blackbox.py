from __future__ import annotations

from collections.abc import Sequence
from math import floor
from typing import Protocol, TypeVar, overload

from numpy import linspace
from typing_extensions import TypeAlias

from ..options import Interval
from .model import Inputs, Model, Trace

S = TypeVar("S", covariant=True)
E = TypeVar("E", covariant=True)

Static: TypeAlias = Sequence[float]
Times: TypeAlias = Sequence[float]
Signals: TypeAlias = Sequence[Sequence[float]]


class Func(Protocol[S, E]):
    def __call__(self, __xs: Static, __ts: Times, __us: Signals) -> tuple[Trace[S], E]:
        ...


class Blackbox(Model[S, E]):
    """General system model which does not make assumptions about the underlying system.

    Attributes:
        func: User-defined function which is given the static parameters, a vector of time values,
              and a matrix of interpolated signal values and returns a SimulationResult or
              Falsification
        sampling_interval: Time-step to use for interpolating signal values over the simulation
                           interval
    """

    def __init__(self, func: Func[S, E], step_size: float):
        self.func = func
        self.step_size = step_size

    def __call__(self, inputs: Inputs, interval: Interval) -> tuple[Trace[S], E]:
        step_count = floor(interval.length / self.step_size)
        signal_times = linspace(start=interval.lower, stop=interval.upper, num=step_count)
        signal_times_list: list[float] = signal_times.tolist()
        signal_values = [signal.at_times(signal_times_list) for signal in inputs.signals]

        return self.func(inputs.static, signal_times_list, signal_values)


class BareFunc(Protocol[S]):
    def __call__(self, __xs: Static, __ts: Times, __us: Signals) -> Trace[S]:
        ...


T = TypeVar("T")
U = TypeVar("U")


class Decorator:
    def __init__(self, step_size: float):
        self.step_size = step_size

    @overload
    def __call__(self, f: BareFunc[T]) -> Blackbox[T, None]:
        ...

    @overload
    def __call__(self, f: Func[T, U]) -> Blackbox[T, U]:
        pass

    def __call__(self, f: BareFunc[T] | Func[T, U]) -> Blackbox[T, U | None]:
        def wrapper(xs: Static, ts: Times, us: Signals) -> tuple[Trace[T], U | None]:
            result = f(xs, ts, us)

            if isinstance(result, Trace):
                return (result, None)

            return result

        return Blackbox(wrapper, self.step_size)


def blackbox(*, step_size: float = 0.1) -> Decorator:
    return Decorator(step_size)
