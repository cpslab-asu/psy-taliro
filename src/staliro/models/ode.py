from __future__ import annotations

from typing import Literal, Protocol, cast

from numpy import array, float_
from numpy.typing import NDArray
from scipy import integrate
from typing_extensions import TypeAlias

from ..options import Interval
from .model import Inputs, Model, Trace

Static: TypeAlias = NDArray[float_]
Signals: TypeAlias = NDArray[float_]


class Func(Protocol):
    def __call__(self, __time: float, __static: Static, __signals: Signals) -> NDArray[float_]:
        ...


class Ode(Model[list[float], None]):
    """Model which assumes the underlying system is modeled by an Ordinary Differential Equation.

    Attributes:
        func: User-defined function which is given a time value, a state, and a vector of signal
              values and returns a new state.
    """
    Method: TypeAlias = Literal["RK45", "RK23", "DOP853", "Radau", "BDF", "LSODA"]

    def __init__(self, func: Func, method: Ode.Method):
        self.func = func
        self.method = method

    def __call__(self, inputs: Inputs, interval: Interval) -> tuple[Trace[list[float]], None]:
        def integration_fn(time: float, state: NDArray[float_]) -> NDArray[float_]:
            return self.func(
                time,
                state,
                array([signal.at_time(time) for signal in inputs.signals]),
            )

        integration = integrate.solve_ivp(
            fun=integration_fn,
            t_span=interval.astuple(),
            y0=inputs.static,
            method=self.method,
        )

        times = cast(list[float], integration.t.tolist())
        states = cast(list[list[float]], integration.y.tolist())
        trace = Trace(times, states)

        return (trace, None)


class Decorator(Protocol):
    def __call__(self, __func: Func) -> Ode:
        ...


def ode(*, method: Ode.Method = "RK45") -> Decorator:
    def decorator(func: Func) -> Ode:
        return Ode(func, method)

    return decorator
