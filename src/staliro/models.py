from __future__ import annotations

import sys
from dataclasses import dataclass
from math import floor
from typing import Tuple, Union

if sys.version_info >= (3, 9):
    from collections.abc import Sequence, Callable
else:
    from typing import Sequence, Callable

if sys.version_info >= (3, 8):
    from typing import Protocol, runtime_checkable
else:
    from typing_extensions import Protocol, runtime_checkable

from numpy import float32, linspace, ndarray, array
from scipy import integrate

from .options import Interval
from .signals import SignalInterpolator


@dataclass(frozen=True)
class Observations:
    _trajectories: ndarray
    _timestamps: ndarray

    def __post_init__(self) -> None:
        if self._timestamps.ndim != 1:
            raise ValueError("timestamps must be 1-dimensional")

        if self._trajectories.ndim != 2:
            raise ValueError("trajectories must be 2-dimensional")

        times_len = self._timestamps.shape[0]
        traj_shape = self._trajectories.shape

        if traj_shape[0] != times_len and traj_shape[1] != times_len:
            raise ValueError("trajectories must have one axis of equal length to timestamps")

    @property
    def timestamps(self) -> ndarray:
        return self._timestamps

    @property
    def trajectories(self) -> ndarray:
        if self._trajectories.shape[0] == self._timestamps.shape[0]:
            return self._trajectories.T

        return self._trajectories


class Falsification:
    pass


StaticParameters = ndarray
SignalInterpolators = Sequence[SignalInterpolator]
ModelResult = Union[Observations, Falsification]


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
BlackboxResult = Union[Observations, Falsification, Tuple[Trajectories, Timestamps]]
BlackboxFunc = Callable[[StaticParameters, SignalTimes, SignalValues], BlackboxResult]


def _make_observation(result: Tuple[Trajectories, Timestamps]) -> Observations:
    if len(result) != 2:
        raise ValueError("Expected tuple to be length 2")

    return Observations(array(result[0]), array(result[1]))


class _Blackbox(Model):
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
        result = self.func(static_params, signal_times, array(signal_traces))

        if isinstance(result, tuple):
            return _make_observation(result)
        elif isinstance(result, (Observations, Falsification)):
            return result
        else:
            raise ValueError("Unknown return type from blackbox")


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


class _ODE(Model):
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


def blackbox(*, sampling_interval: float = 0.1) -> Callable[[BlackboxFunc], _Blackbox]:
    return lambda f: _Blackbox(f, sampling_interval)


def ode() -> Callable[[ODEFunc], _ODE]:
    return _ODE
