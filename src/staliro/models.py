from __future__ import annotations

import math
from typing import Callable, List, Optional, Sequence, TypeVar, Union

import numpy as np
from numpy.typing import NDArray
from scipy import integrate
from typing_extensions import Literal, overload

from .core.interval import Interval
from .core.model import Model, ModelResult, ModelData, StaticInput
from .core.signal import Signal

StateT = TypeVar("StateT")
ExtraT = TypeVar("ExtraT")

Signals = Sequence[Signal]
StaticParameters = Sequence[float]
SignalTimes = NDArray[np.float_]
SignalValues = NDArray[np.float_]
BlackboxFunc = Callable[[StaticParameters, SignalTimes, SignalValues], ModelResult[StateT, ExtraT]]


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

    def simulate(
        self, static: StaticInput, signals: Signals, interval: Interval
    ) -> ModelResult[StateT, ExtraT]:
        step_count = math.floor(interval.length / self.sampling_interval)
        signal_times = np.linspace(start=interval.lower, stop=interval.upper, num=step_count)
        signal_times_list: List[float] = signal_times.tolist()
        signal_traces = [signal.at_times(signal_times_list) for signal in signals]

        return self.func(static, signal_times, np.array(signal_traces))


Time = float
State = NDArray[np.float_]
IntegrationFn = Callable[[Time, State], State]
ODEFunc = Callable[[Time, State, SignalValues], State]
ODEData = ModelData[NDArray[np.float_], None]


class IntegrationFunc:
    def __init__(self, signals: Sequence[Signal], ode_func: ODEFunc):
        self.signals = signals
        self.func = ode_func

    def __call__(self, time: Time, state: State) -> State:
        signal_values = np.array([signal.at_time(time) for signal in self.signals])
        return self.func(time, state, signal_values)


_MethodT = Literal["RK45", "RK23", "DOP853", "Radau", "BDF", "LSODA"]


class ODE(Model[NDArray[np.float_], None]):
    """Model which assumes the underlying system is modeled by an Ordinary Differential Equation.

    Attributes:
        func: User-defined function which is given a time value, a state, and a vector of signal
              values and returns a new state.
    """

    def __init__(self, func: ODEFunc, method: _MethodT):
        self.func = func
        self.method = method

    def simulate(self, static: StaticInput, signals: Signals, interval: Interval) -> ODEData:
        integration_fn = IntegrationFunc(signals, self.func)
        integration = integrate.solve_ivp(
            fun=integration_fn,
            t_span=interval.astuple(),
            y0=static,
            method=self.method,
        )

        return ModelData(integration.y, integration.t)


_BlackboxDecorator = Callable[[BlackboxFunc[StateT, ExtraT]], Blackbox[StateT, ExtraT]]


@overload
def blackbox(
    *, sampling_interval: float = ...
) -> Callable[[BlackboxFunc[StateT, ExtraT]], Blackbox[StateT, ExtraT]]:
    ...


@overload
def blackbox(_func: BlackboxFunc[StateT, ExtraT]) -> Blackbox[StateT, ExtraT]:
    ...


def blackbox(
    _func: Optional[BlackboxFunc[StateT, ExtraT]] = None, *, sampling_interval: float = 0.1
) -> Union[Blackbox[StateT, ExtraT], _BlackboxDecorator[StateT, ExtraT]]:
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


_ODEDecorator = Callable[[ODEFunc], ODE]


@overload
def ode(*, method: _MethodT = ...) -> _ODEDecorator:
    ...


@overload
def ode(_func: ODEFunc) -> ODE:
    ...


def ode(_func: Optional[ODEFunc] = None, *, method: _MethodT = "RK45") -> Union[_ODEDecorator, ODE]:
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
