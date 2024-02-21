from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from typing import Literal, TypeVar, cast, overload

import numpy as np
from numpy.typing import NDArray
from scipy import integrate
from typing_extensions import TypeAlias

from .core.interval import Interval
from .core.model import BasicResult, Model, ModelInputs, ModelResult, Trace
from .core.signal import Signal

StateT = TypeVar("StateT")
ExtraT = TypeVar("ExtraT")

Signals: TypeAlias = Sequence[Signal]
StaticParameters: TypeAlias = Sequence[float]
SignalTimes: TypeAlias = NDArray[np.float_]
SignalValues: TypeAlias = NDArray[np.float_]
BlackboxFunc: TypeAlias = Callable[
    [StaticParameters, SignalTimes, SignalValues], ModelResult[StateT, ExtraT]
]


class Blackbox(Model[StateT, ExtraT]):
    """General system model which does not make assumptions about the underlying system.

    Attributes:
        func: User-defined function which is given the static parameters, a vector of time values,
              and a matrix of interpolated signal values and returns a SimulationResult or
              Falsification
        sampling_interval: Time-step to use for interpolating signal values over the simulation
                           interval
    """

    def __init__(self, func: BlackboxFunc[StateT, ExtraT], sampling_interval: float):
        self.func = func
        self.sampling_interval = sampling_interval

    def simulate(self, inputs: ModelInputs, interval: Interval) -> ModelResult[StateT, ExtraT]:
        step_count = math.floor(interval.length / self.sampling_interval)
        signal_times = np.linspace(start=interval.lower, stop=interval.upper, num=step_count)
        signal_times_list: list[float] = signal_times.tolist()
        signal_traces = [signal.at_times(signal_times_list) for signal in inputs.signals]

        return self.func(inputs.static, signal_times, np.array(signal_traces))


State = NDArray[np.float_]
IntegrationFn = Callable[[float, State], State]
ODEFunc = Callable[[float, State, SignalValues], State]
ODEResult = ModelResult[list[float], None]


class IntegrationFunc:
    def __init__(self, signals: Sequence[Signal], ode_func: ODEFunc):
        self.signals = signals
        self.func = ode_func

    def __call__(self, time: float, state: State) -> State:
        signal_values = np.array([signal.at_time(time) for signal in self.signals])
        return self.func(time, state, signal_values)


_Method: TypeAlias = Literal["RK45", "RK23", "DOP853", "Radau", "BDF", "LSODA"]


class ODE(Model[list[float], None]):
    """Model which assumes the underlying system is modeled by an Ordinary Differential Equation.

    Attributes:
        func: User-defined function which is given a time value, a state, and a vector of signal
              values and returns a new state.
    """

    def __init__(self, func: ODEFunc, method: _Method):
        self.func = func
        self.method = method

    def simulate(self, inputs: ModelInputs, interval: Interval) -> ODEResult:
        integration_fn = IntegrationFunc(inputs.signals, self.func)
        integration = integrate.solve_ivp(
            fun=integration_fn, t_span=interval.astuple(), y0=inputs.static, method=self.method
        )
        times = cast(list[float], integration.t.tolist())
        states = cast(list[list[float]], integration.y.tolist())
        trace = Trace(times, states)

        return BasicResult(trace)


_BlackboxDecorator: TypeAlias = Callable[[BlackboxFunc[StateT, ExtraT]], Blackbox[StateT, ExtraT]]


@overload
def blackbox(
    *, sampling_interval: float = ...
) -> Callable[[BlackboxFunc[StateT, ExtraT]], Blackbox[StateT, ExtraT]]:
    ...


@overload
def blackbox(_func: BlackboxFunc[StateT, ExtraT]) -> Blackbox[StateT, ExtraT]:
    ...


def blackbox(
    _func: BlackboxFunc[StateT, ExtraT] | None = None, *, sampling_interval: float = 0.1
) -> Blackbox[StateT, ExtraT] | _BlackboxDecorator[StateT, ExtraT]:
    """Decorate a function as a blackbox model.

    This decorator can be used with or without arguments.

    Args:
        func: The function to wrap as a blackbox
        *: Variable length argument list
        sampling_interval: The time interval to use when sampling the signal interpolators

    Returns:
        A blackbox model
    """

    def decorator(func: BlackboxFunc[StateT, ExtraT]) -> Blackbox[StateT, ExtraT]:
        return Blackbox(func, sampling_interval)

    if _func is not None:
        return decorator(_func)
    else:
        return decorator


_ODEDecorator: TypeAlias = Callable[[ODEFunc], ODE]


@overload
def ode(*, method: _Method = ...) -> _ODEDecorator:
    ...


@overload
def ode(_func: ODEFunc) -> ODE:
    ...


def ode(_func: ODEFunc | None = None, *, method: _Method = "RK45") -> _ODEDecorator | ODE:
    """Decorate a function as an ODE model.

    This decorator can be used with or without arguments.

    Args:
        _func: The function to wrap as an ODE model

    Returns:
        An ODE model
    """

    def decorator(func: ODEFunc) -> ODE:
        return ODE(func, method)

    if _func is not None:
        return decorator(_func)
    else:
        return decorator
