from __future__ import annotations

from abc import ABC
from typing import Callable, List, Literal, overload, Sequence, Type, Tuple, Union

from numpy import float32, linspace, ndarray, array
from scipy import integrate

from .options import StaliroOptions
from .signals import SignalInterpolator


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


def _signal_trace(interpolator: SignalInterpolator, times: ndarray) -> ndarray:
    return array(interpolator.interpolate(times))


ModelResult = Tuple[ndarray, ndarray]


class Model(ABC):
    def simulate(self, values: ndarray, options: StaliroOptions) -> ModelResult:
        raise NotImplementedError()


StaticParameters = ndarray
SignalTimes = ndarray
SignalValues = ndarray

Timestamps = Union[ndarray, Sequence[float]]
Trajectories = Union[ndarray, Sequence[Sequence[float]]]
BlackboxResult = Tuple[Trajectories, Timestamps]

BlackboxFunc = Callable[[StaticParameters, SignalTimes, SignalValues], BlackboxResult]
InterpolatorBlackboxFunc = Callable[
    [StaticParameters, Sequence[SignalInterpolator]], BlackboxResult
]


class Blackbox(Model):
    def __init__(self, func: BlackboxFunc):
        self.func = func

    def simulate(self, values: ndarray, options: StaliroOptions) -> ModelResult:
        interval = options.interval
        duration = interval.upper - interval.lower
        point_count = duration / options.sampling_interval

        static_params = _static_parameters(values, options)
        interpolators = _signal_interpolators(values, options)
        signal_times = linspace(
            start=interval.lower, stop=interval.upper, num=int(point_count), endpoint=True
        )
        signal_traces = [
            _signal_trace(interpolator, signal_times) for interpolator in interpolators
        ]
        trajectories, timestamps = self.func(static_params, signal_times, array(signal_traces))

        return array(trajectories), array(timestamps)


class InterpolatorBlackbox(Model):
    def __init__(self, func: InterpolatorBlackboxFunc):
        self.func = func

    def simulate(self, values: ndarray, options: StaliroOptions) -> ModelResult:
        static_params = _static_parameters(values, options)
        interpolators = _signal_interpolators(values, options)
        trajectories, timestamps = self.func(static_params, interpolators)

        return array(trajectories), array(timestamps)


Time = float
State = ndarray
ODEResult = Union[ndarray, Sequence[float]]
ODEFunc = Callable[[Time, State, SignalValues], ODEResult]


class ODE(Model):
    def __init__(self, func: ODEFunc):
        self.func = func

    def simulate(self, values: ndarray, options: StaliroOptions) -> ModelResult:
        static_params = _static_parameters(values, options)
        interpolators = _signal_interpolators(values, options)

        def integration_fn(time: float, state: ndarray) -> ndarray:
            signal_values = [interpolator.interpolate(time) for interpolator in interpolators]
            new_state = self.func(time, state, array(signal_values))

            return array(new_state)

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
