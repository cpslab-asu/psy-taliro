from __future__ import annotations

import sys
from dataclasses import dataclass
from math import floor
from typing import Tuple, Union, Optional

if sys.version_info >= (3, 9):
    from collections.abc import Sequence, Callable
else:
    from typing import Sequence, Callable

if sys.version_info >= (3, 8):
    from typing import Protocol, runtime_checkable, overload
else:
    from typing_extensions import Protocol, runtime_checkable, overload

from numpy import linspace, ndarray, array, atleast_2d
from scipy import integrate

from .options import Interval
from .signals import SignalInterpolator


@dataclass(frozen=True)
class SimulationResult:
    _trajectories: ndarray
    _timestamps: ndarray

    def __post_init__(self) -> None:
        if self._timestamps.ndim != 1:
            raise ValueError("timestamps must be 1-dimensional")

        if not 1 <= self._trajectories.ndim <= 2:
            raise ValueError("expected 1 or 2-dimensional trajectories")

        if not any(dim == self._timestamps.shape[0] for dim in self._trajectories.shape):
            raise ValueError("expected one dimension to match timestamps length")

    @property
    def timestamps(self) -> ndarray:
        return self._timestamps

    @property
    def trajectories(self) -> ndarray:
        _trajectories = atleast_2d(self._trajectories)

        if _trajectories.shape[0] == self._timestamps.shape[0]:
            return _trajectories.T

        return _trajectories


class Falsification:
    pass


StaticParameters = ndarray
SignalInterpolators = Sequence[SignalInterpolator]


@runtime_checkable
class Model(Protocol):
    def simulate(
        self,
        __static_params: StaticParameters,
        __interpolators: SignalInterpolators,
        __interval: Interval,
    ) -> Union[SimulationResult, Falsification]:
        ...


SignalTimes = ndarray
SignalValues = ndarray
Timestamps = Union[ndarray, Sequence[float]]
Trajectories = Union[ndarray, Sequence[Sequence[float]]]
BlackboxResult = Union[SimulationResult, Falsification, Tuple[Trajectories, Timestamps]]
_BlackboxFunc = Callable[[StaticParameters, SignalTimes, SignalValues], BlackboxResult]


class _Blackbox(Model):
    def __init__(self, func: _BlackboxFunc, sampling_interval: float = 0.1):
        self.func = func
        self.sampling_interval = sampling_interval

    def simulate(
        self,
        static_params: StaticParameters,
        interpolators: SignalInterpolators,
        interval: Interval,
    ) -> Union[SimulationResult, Falsification]:
        duration = interval.upper - interval.lower
        point_count = floor(duration / self.sampling_interval)
        signal_times = linspace(start=interval.lower, stop=interval.upper, num=point_count)
        signal_traces = [interpolator.interpolate(signal_times) for interpolator in interpolators]
        result = self.func(static_params, signal_times, array(signal_traces))

        if isinstance(result, tuple):
            return SimulationResult(array(result[0]), array(result[1]))

        return result


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
    ) -> Union[SimulationResult, Falsification]:
        integration_fn = _make_integration_fn(interpolators, self.func)
        integration = integrate.solve_ivp(integration_fn, interval.astuple(), static_params)

        return SimulationResult(integration.y, integration.t)


_BlackboxDecorator = Callable[[_BlackboxFunc], _Blackbox]


@overload
def blackbox(*, sampling_interval: float = ...) -> _BlackboxDecorator:
    ...


@overload
def blackbox(_func: _BlackboxFunc) -> _Blackbox:
    ...


def blackbox(
    _func: Optional[_BlackboxFunc] = None, *, sampling_interval: float = 0.1
) -> Union[_Blackbox, _BlackboxDecorator]:
    """Decorate a function as a blackbox model.

    This decorator can be used with or without arguments.

    Args:
        func: The function to wrap as a blackbox
        *: Variable length argument list
        sampling_interval: The time interval to use when sampling the signal interpolators

    Returns:
        A blackbox model
    """

    def decorator(func: _BlackboxFunc) -> _Blackbox:
        return _Blackbox(func, sampling_interval)

    if _func is not None:
        return _Blackbox(_func, sampling_interval)
    else:
        return decorator


def ode() -> Callable[[ODEFunc], _ODE]:
    return _ODE
