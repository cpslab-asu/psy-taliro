from __future__ import annotations

import sys
from math import floor
from typing import Callable, Sequence, Type, Tuple, Union

if sys.version_info > (3, 8):
    from typing import Protocol, runtime_checkable
else:
    from typing_extensions import Protocol, runtime_checkable

from numpy import float32, linspace, ndarray, array
from scipy import integrate

from .options import Interval
from .signals import SignalInterpolator

ModelResult = Tuple[ndarray, ndarray]
StaticParameters = ndarray
SignalInterpolators = Sequence[SignalInterpolator]


@runtime_checkable
class Model(Protocol):
    def simulate(
        self,
        __static_params: StaticParameters,
        __interpolators: SignalInterpolators,
        __interval: Interval,
    ) -> ModelResult:
        ...


SignalTimes = ndarray
SignalValues = ndarray
Timestamps = Union[ndarray, Sequence[float]]
Trajectories = Union[ndarray, Sequence[Sequence[float]]]
BlackboxResult = Tuple[Trajectories, Timestamps]
BlackboxFunc = Callable[[StaticParameters, SignalTimes, SignalValues], BlackboxResult]


class Blackbox(Model):
    def __init__(self, func: BlackboxFunc, sampling_interval: float = 0.1):
        self.func = func
        self.sampling_interval = sampling_interval

    def simulate(
        self,
        static_params: StaticParameters,
        interpolators: SignalInterpolators,
        interval: Interval,
    ) -> ModelResult:
        duration = interval.upper - interval.lower
        point_count = floor(duration / self.sampling_interval)
        signal_times = linspace(start=interval.lower, stop=interval.upper, num=point_count)
        signal_traces = [interpolator.interpolate(signal_times) for interpolator in interpolators]
        trajectories, timestamps = self.func(static_params, signal_times, array(signal_traces))

        return array(trajectories), array(timestamps)


Time = float
State = ndarray
ODEResult = Union[ndarray, Sequence[float]]
ODEFunc = Callable[[Time, State, SignalValues], ODEResult]


class ODE(Model):
    def __init__(self, func: ODEFunc):
        self.func = func

    def simulate(
        self,
        static_params: StaticParameters,
        interpolators: SignalInterpolators,
        interval: Interval,
    ) -> ModelResult:
        def integration_fn(time: float, state: ndarray) -> ndarray:
            signal_values = [interpolator.interpolate(time) for interpolator in interpolators]
            return array(self.func(time, state, array(signal_values)))

        integration = integrate.solve_ivp(integration_fn, interval.astuple(), static_params)
        return integration.y, integration.t.astype(float32)


BlackboxFactory = Callable[[BlackboxFunc], Blackbox]


def blackbox(*, interpolated: bool = True, sampling_interval: float = 0.1) -> BlackboxFactory:
    return lambda x: Blackbox(x, sampling_interval)


def ode() -> Type[ODE]:
    return ODE
