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
IntegrationFn = Callable[[float, ndarray], ndarray]
ODEResult = Union[ndarray, Sequence[float]]
ODEFunc = Callable[[Time, State, SignalValues], ODEResult]


def _make_integration_fn(signals: SignalInterpolators, func: ODEFunc) -> IntegrationFn:
    def integration_fn(time: float, state: ndarray) -> ndarray:
        signal_values = [signal.interpolate(time) for signal in signals]
        result = func(time, state, array(signal_values))

        return array(result)

    return integration_fn


class ODE(Model):
    def __init__(self, func: ODEFunc):
        self.func = func

    def simulate(
        self,
        static_params: StaticParameters,
        interpolators: SignalInterpolators,
        interval: Interval,
    ) -> ModelResult:
        integration_fn = _make_integration_fn(interpolators, self.func)
        integration = integrate.solve_ivp(integration_fn, interval.astuple(), static_params)

        return integration.y, integration.t.astype(float32)


BlackboxFactory = Callable[[BlackboxFunc], Blackbox]


def blackbox(*, sampling_interval: float = 0.1) -> BlackboxFactory:
    return lambda f: Blackbox(f, sampling_interval)


def ode() -> Type[ODE]:
    return ODE
