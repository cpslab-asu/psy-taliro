from __future__ import annotations

from abc import ABC
from typing import Callable, List, Literal, overload, Sequence, Type, Tuple, Union

from numpy import float32, linspace, ndarray
from scipy import integrate

from .options import StaliroOptions
from .signals import SignalInterpolator

Trajectories = Union[ndarray, Sequence[Sequence[float]]]
Timestamps = Union[Sequence[float], ndarray]
SimulationResult = Tuple[Trajectories, Timestamps]
StaticParameters = Union[Sequence[float], ndarray]
SignalValues = Union[Sequence[float], ndarray]


def _static_parameters(values: ndarray, options: StaliroOptions) -> ndarray:
    stop = len(options.static_parameters)
    return values[0:stop]  # type: ignore


def _signal_interpolators(values: ndarray, options: StaliroOptions) -> List[SignalInterpolator]:
    start = len(options.static_parameters)
    interpolators: List[SignalInterpolator] = []

    for signal in options.signals:
        factory = signal.factory
        end = start + signal.control_points
        interpolators.append(factory.create(signal.interval.astuple(), values[start:end]))
        start = end

    return interpolators


def _signal_trace(interpolator: SignalInterpolator, times: Sequence[float]) -> List[float]:
    return [interpolator.interpolate(time) for time in times]


class Model(ABC):
    def simulate(self, values: ndarray, options: StaliroOptions) -> SimulationResult:
        raise NotImplementedError()


BlackboxFunc = Callable[[StaticParameters, Timestamps, Sequence[SignalValues]], SimulationResult]


class Blackbox(Model):
    def __init__(self, func: BlackboxFunc):
        self.func = func

    def simulate(self, values: ndarray, options: StaliroOptions) -> SimulationResult:
        interval = options.interval
        duration = interval.upper - interval.lower
        point_count = duration / options.sampling_interval

        static_params = _static_parameters(values, options)
        interpolators = _signal_interpolators(values, options)
        signal_times = linspace(
            start=interval.lower, stop=interval.upper, num=point_count, endpoint=True
        )  # type: ignore
        signal_traces = [
            _signal_trace(interpolator, signal_times) for interpolator in interpolators
        ]

        return self.func(static_params, signal_times, signal_traces)


InterpolatorBlackboxFunc = Callable[
    [StaticParameters, Sequence[SignalInterpolator]], SimulationResult
]


class InterpolatorBlackbox(Model):
    def __init__(self, func: InterpolatorBlackboxFunc):
        self.func = func

    def simulate(self, values: ndarray, options: StaliroOptions) -> SimulationResult:
        static_params = _static_parameters(values, options)
        interpolators = _signal_interpolators(values, options)

        return self.func(static_params, interpolators)


State = Sequence[float]
ODEFunc = Callable[[float, State, SignalValues], State]


class ODE(Model):
    def __init__(self, func: ODEFunc):
        self.func = func

    def simulate(self, values: ndarray, options: StaliroOptions) -> SimulationResult:
        static_params = _static_parameters(values, options)
        interpolators = _signal_interpolators(values, options)

        def integration_fn(time: float, state: ndarray) -> Sequence[float]:
            signal_values = [interpolator.interpolate(time) for interpolator in interpolators]
            return self.func(time, tuple(state), signal_values)

        interval = options.interval.astuple()
        integration = integrate.solve_ivp(integration_fn, interval, static_params)

        return integration.y, integration.t.astype(float32)


@overload
def blackbox(*, interpolated: Literal[False]) -> Type[InterpolatorBlackbox]:
    ...


@overload
def blackbox(*, interpolated: Literal[True] = ...) -> Type[Blackbox]:
    ...


def blackbox(*, interpolated: bool = True) -> Union[Type[Blackbox], Type[InterpolatorBlackbox]]:
    if not interpolated:
        return InterpolatorBlackbox
    else:
        return Blackbox


def ode() -> Type[ODE]:
    return ODE
