from __future__ import annotations

from math import floor
from typing import Protocol, TypeVar, Union, overload

from attrs import frozen
from numpy import linspace
from typing_extensions import TypeAlias

from .model import Model, Result, Sample, Trace

S = TypeVar("S", covariant=True)
E = TypeVar("E", covariant=True)


class UserResultFunc(Protocol[S, E]):
    def __call__(self, __inputs: Blackbox.Inputs) -> Result[Trace[S], E]:
        ...


class UserTraceFunc(Protocol[S]):
    def __call__(self, __inputs: Blackbox.Inputs) -> Trace[S]:
        ...


class Blackbox(Model[S, Union[E, None]]):
    """General system model which does not make assumptions about the underlying system.

    Attributes:
        func: User-defined function which is given the static parameters, a vector of time values,
              and a matrix of interpolated signal values and returns a SimulationResult or
              Falsification
        sampling_interval: Time-step to use for interpolating signal values over the simulation
                           interval
    """

    @frozen(slots=True)
    class Inputs:
        static: dict[str, float]
        times: list[float]
        signals: dict[str, list[float]]

    def __init__(self, func: UserResultFunc[S, E] | UserTraceFunc[S], step_size: float):
        self.func = func
        self.step_size = step_size

    def simulate(self, sample: Sample) -> Result[Trace[S], E | None]:
        tstart, tend = sample.signals.tspan
        duration = tend - tstart
        step_count = floor(duration / self.step_size)

        times: list[float] = linspace(tstart, tend, num=step_count, dtype=float).tolist()
        signals = {name: sample.signals[name].at_times(times) for name in sample.signals.names}
        result = self.func(Blackbox.Inputs(sample.static, times, signals))

        if isinstance(result, Trace):
            return Result(result, None)

        if isinstance(result, Result):
            return result

        raise TypeError("Blackbox function must return Result or Trace")


class Decorator(Protocol):
    @overload
    def __call__(self, __func: UserResultFunc[S, E]) -> Blackbox[S, E]:
        ...

    @overload
    def __call__(self, __func: UserTraceFunc[S]) -> Blackbox[S, None]:
        ...


UserFunc: TypeAlias = Union[UserTraceFunc[S], UserResultFunc[S, E]]


def blackbox(*, step_size: float = 0.1) -> Decorator:
    @overload
    def _decorator(func: UserResultFunc[S, E]) -> Blackbox[S, E]:
        ...

    @overload
    def _decorator(func: UserTraceFunc[S]) -> Blackbox[S, None]:
        ...

    def _decorator(func: UserFunc[S, E]) -> Blackbox[S, E | None]:
        return Blackbox(func, step_size)

    return _decorator


__all__ = ["Blackbox", "blackbox"]
