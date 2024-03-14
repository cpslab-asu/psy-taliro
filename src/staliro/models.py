from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from math import floor
from typing import Generic, Literal, SupportsFloat, TypeVar, Union, cast, overload

from attrs import frozen
from numpy import array, float_, linspace
from numpy.typing import NDArray
from scipy import integrate
from sortedcontainers import SortedDict
from typing_extensions import TypeAlias

from .cost_func import FuncWrapper, Sample
from .cost_func import Result as _Result

S = TypeVar("S", covariant=True)
E = TypeVar("E", covariant=True)
R = TypeVar("R", covariant=True)


class Trace(Generic[S], Iterable[tuple[float, S]]):
    @overload
    def __init__(self, *, times: Iterable[SupportsFloat], states: Iterable[S]): ...

    @overload
    def __init__(self, states: Mapping[SupportsFloat, S], /): ...

    def __init__(
        self,
        times: Iterable[SupportsFloat] | Mapping[SupportsFloat, S],
        states: Iterable[S] | None = None,
    ):
        if not isinstance(times, Mapping):
            if states is None:
                raise ValueError("Must provide states with times")

            times_ = [float(time) for time in times]
            states_ = list(states)

            if len(times_) != len(states_):
                raise ValueError("length of times and states iterables must be the same")

            self.elements = SortedDict(zip(times_, states_))
        else:
            self.elements = SortedDict({float(time): state for time, state in times.items()})

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Trace):
            return NotImplemented

        return self.elements == other.elements

    def __len__(self) -> int:
        return len(self.elements)

    def __iter__(self) -> Iterator[tuple[float, S]]:
        return iter(self.elements.items())

    def __getitem__(self, time: float) -> S:
        return cast(S, self.elements[time])

    @property
    def times(self) -> Iterator[float]:
        return iter(self.elements.keys())

    @property
    def states(self) -> Iterator[S]:
        return iter(self.elements.values())


class Result(Generic[S, E], _Result[Trace[S], E]):
    @overload
    def __init__(self, trace: Mapping[SupportsFloat, S], /, extra: E):
        ...

    @overload
    def __init__(self, *, states: Iterable[S], times: Iterable[SupportsFloat], extra: E):
        ...

    def __init__(
        self,
        states: Mapping[SupportsFloat, S] | Iterable[S],
        extra: E,
        times: Iterable[SupportsFloat] | None = None,
    ):
        if isinstance(states, Mapping):
            trace = Trace(states)
        else:
            if times is None:
                raise ValueError("Must provide times if states is not a dict")

            trace = Trace(states=states, times = times)

        super().__init__(trace, extra)


class Model(Generic[S, E], ABC):
    """Representation of the system under test (SUT)."""

    @abstractmethod
    def simulate(self, sample: Sample) -> _Result[Trace[S], E]: ...


class ModelWrapper(Model[S, E]):
    def __init__(self, func: Callable[[Sample], _Result[Trace[S], E]]):
        self.func = func

    def simulate(self, sample: Sample) -> _Result[Trace[S], E]:
        return self.func(sample)


ModelFunc: TypeAlias = Union[
    Callable[[Sample], _Result[Trace[S], E]],
    Callable[[Sample], Trace[R]],
]


class ModelDecorator:
    @overload
    def __call__(self, func: Callable[[Sample], _Result[Trace[S], E]]) -> ModelWrapper[S, E]: ...

    @overload
    def __call__(self, func: Callable[[Sample], Trace[R]]) -> ModelWrapper[R, None]: ...

    def __call__(self, func: ModelFunc[S, E, R]) -> ModelWrapper[S, E] | ModelWrapper[R, None]:
        return ModelWrapper(FuncWrapper(func))


@overload
def model(func: Callable[[Sample], _Result[Trace[S], E]]) -> ModelWrapper[S, E]: ...


@overload
def model(func: Callable[[Sample], Trace[R]]) -> ModelWrapper[R, None]: ...


@overload
def model(func: None = ...) -> ModelDecorator: ...


def model(
    func: ModelFunc[S, E, R] | None = None,
) -> ModelWrapper[S, E] | ModelWrapper[R, None] | ModelDecorator:
    decorator = ModelDecorator()

    if func:
        return decorator(func)

    return decorator


class Blackbox(Model[S, E]):
    """General system model which does not make assumptions about the underlying system.

    Attributes:
        func: User-defined function which is given the static parameters, a vector of time values,
              and a matrix of interpolated signal values and returns a SimulationResult or
              Falsification
        sampling_interval: Time-step to use for interpolating signal values over the simulation
                           interval
    """

    @frozen(slots=True)
    class Inputs:
        """Interpolated inputs to a Blackbox model.

        The times attributes will always contain as keys all of the interpolation times for the
        given `~TestOptions.tspan`. If no `~TestOptions.signals` are defined, then the value for
        each time will be an empty dictionary.

        Attributes:
            static: The static (time-invariant) inputs to the system
            times: Mapping from each interpolation time to the values of each signal at that time
        """

        static: dict[str, float]
        times: dict[float, dict[str, float]]

    def __init__(self, func: Callable[[Blackbox.Inputs], _Result[Trace[S], E]], step_size: float):
        self._func = func
        self.step_size = step_size

    def _create_inputs(self, sample: Sample) -> Blackbox.Inputs:
        if sample.signals.tspan:
            tstart, tend = sample.signals.tspan
            duration = tend - tstart
            step_count = floor(duration / self.step_size) + 1

            times: list[float] = linspace(tstart, tend, num=step_count, dtype=float).tolist()
            signals = {
                time: {name: sample.signals[name].at_time(time) for name in sample.signals.names}
                for time in times
            }
        else:
            signals = {}

        return Blackbox.Inputs(sample.static, signals)

    def simulate(self, sample: Sample) -> _Result[Trace[S], E]:
        return self._func(self._create_inputs(sample))


BlackboxFunc: TypeAlias = Union[
    Callable[[Blackbox.Inputs], _Result[Trace[S], E]],
    Callable[[Blackbox.Inputs], Trace[R]],
]


class BlackboxDecorator:
    def __init__(self, step_size: float):
        self.step_size = step_size

    @overload
    def __call__(
        self, func: Callable[[Blackbox.Inputs], _Result[Trace[S], E]]
    ) -> Blackbox[S, E]: ...

    @overload
    def __call__(self, func: Callable[[Blackbox.Inputs], Trace[R]]) -> Blackbox[R, None]: ...

    def __call__(self, func: BlackboxFunc[S, E, R]) -> Blackbox[S, E] | Blackbox[R, None]:
        return Blackbox(FuncWrapper(func), self.step_size)


@overload
def blackbox(
    func: Callable[[Blackbox.Inputs], _Result[Trace[S], E]],
    *,
    step_size: float = ...,
) -> Blackbox[S, E]: ...


@overload
def blackbox(
    func: Callable[[Blackbox.Inputs], Trace[R]],
    *,
    step_size: float = ...,
) -> Blackbox[R, None]: ...


@overload
def blackbox(func: None = ..., *, step_size: float = ...) -> BlackboxDecorator: ...


def blackbox(
    func: BlackboxFunc[S, E, R] | None = None,
    *,
    step_size: float = 0.1,
) -> Blackbox[S, E] | Blackbox[R, None] | BlackboxDecorator:
    decorator = BlackboxDecorator(step_size)

    if func:
        return decorator(func)

    return decorator


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

    def __init__(
        self, func: Callable[[Ode.Inputs], Sequence[float] | NDArray[float_]], method: Ode.Method
    ):
        self.func = func
        self.method = method

    def simulate(self, sample: Sample) -> Result[Trace[list[float]], None]:
        if sample.signals.tspan is None:
            raise RuntimeError("ODE model requires tspan to be defined in TestOptions")

        def integration_fn(time: float, state: NDArray[float_]) -> NDArray[float_]:
            static = {name: state[idx] for idx, name in enumerate(sample.static)}
            signals = {name: sample.signals[name].at_time(time) for name in sample.signals.names}
            deriv = self.func(Ode.Inputs(time, static, signals))

            return array(deriv)

        integration = integrate.solve_ivp(
            fun=integration_fn,
            t_span=sample.signals.tspan,
            y0=[sample.static[name] for name in sample.static],
            method=self.method,
        )

        return Result(
            value=Trace(
                times=integration.t.tolist(),
                states=integration.y.T.astype(dtype=float).tolist(),
            ),
            extra=None,
        )


class OdeDecorator:
    def __init__(self, method: Ode.Method):
        self.method = method

    def __call__(self, func: Callable[[Ode.Inputs], Sequence[float] | NDArray[float_]]) -> Ode:
        return Ode(func, self.method)


@overload
def ode(
    func: Callable[[Ode.Inputs], Sequence[float] | NDArray[float_]], *, method: Ode.Method = ...
) -> Ode: ...


@overload
def ode(func: None = ..., *, method: Ode.Method = ...) -> OdeDecorator:
    pass


def ode(
    func: Callable[[Ode.Inputs], Sequence[float] | NDArray[float_]] | None = None,
    *,
    method: Ode.Method = "RK45",
) -> Ode | OdeDecorator:
    decorator = OdeDecorator(method)

    if func:
        return decorator(func)

    return decorator
