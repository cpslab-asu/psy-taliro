from __future__ import annotations

from collections.abc import Sequence
from typing import Literal, Protocol

from attrs import frozen
from numpy import array, float_, ndarray
from numpy.typing import NDArray
from scipy import integrate
from typing_extensions import TypeAlias

from .model import Model, Result, Sample, Trace


class UserFunc(Protocol):
    def __call__(self, __inputs: Ode.Inputs) -> Sequence[float] | NDArray[float_]:
        ...


class Ode(Model[list[float], None]):
    """Model which assumes the underlying system is modeled by an Ordinary Differential Equation.

    Attributes:
        func: User-defined function which is given a time value, a state, and a vector of signal
              values and returns a new state.
    """
    Method: TypeAlias = Literal["RK45", "RK23", "DOP853", "Radau", "BDF", "LSODA"]

    @frozen(slots=True)
    class Inputs:
        time: float
        state: dict[str, float]
        signals: dict[str, float]

    def __init__(self, func: UserFunc, method: Ode.Method):
        self.func = func
        self.method = method

    def simulate(self, sample: Sample) -> Result[Trace[list[float]], None]:
        order = list(sample.static.keys())
        static = [sample.static[name] for name in order]

        def integration_fn(time: float, state: NDArray[float_]) -> NDArray[float_]:
            static = {name: state[idx] for idx, name in enumerate(order)}
            signals = {name: sample.signals[name].at_time(time) for name in sample.signals.names}
            deriv = self.func(Ode.Inputs(time, static, signals))

            if not isinstance(deriv, ndarray):
                return array(deriv)

            return deriv

        integration = integrate.solve_ivp(
            fun=integration_fn,
            t_span=sample.signals.tspan,
            y0=static,
            method=self.method,
        )

        times: list[float] = integration.t.tolist()
        states: list[list[float]] = integration.y.tolist()
        trace = Trace(times, states)

        return Result(trace, None)


class Decorator(Protocol):
    def __call__(self, func: UserFunc) -> Ode:
        ...


def ode(*, method: Ode.Method = "RK45") -> Decorator:
    def _decorator(func: UserFunc) -> Ode:
        return Ode(func, method)

    return _decorator
