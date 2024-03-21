"""
Simulate systems into traces of timed system states.

The `Model` class represents the logic for simulating the system under test and producing a set of
time-indexed system states called at `Trace`. The `Sample` created by the `Optimizer` is provided as
input to the system, which must create a trace as output. The `evaluate` method of the model must
return a `staliro.Result` value containing the output trace, which can be simplified by constructing
a `models.Result` which accepts the arguments for both a ``Trace`` and a ``staliro.Result``.

Examples
--------

::

    from staliro import Sample, Result, models

    trace = models.Trace({1.0: [4.5, 2.7]})
    trace = models.Trace(times=[1.0, 2.0], states=[[4.5, 2.7], [1.0, 3.0]])


    class Model(models.Model[list[float], None]):
        def evaluate(self, sample: Sample) -> Result[Trace[list[float], None]]:
            states = {
                1.0: [4.5, 2.7],
                2.0: [1.0, 3.0],
            }

            return Result(models.Trace(states), None)


    @models.model
    def model(sample: Sample) -> models.Result[list[float], None]:
        return models.Result(times=[1.0, 2.0], states=[[4.5, 2.7], [1.0, 3.0]], extra=None)

Blackbox
--------

Instead of providing the input signals as continuous functions, the `Blackbox` model evaluates the
signals at a fixed-size time step and provides the matrix of times and evaluated signals as system
inputs instead. A ``Blackbox`` model can be constructed by applying the `blackbox()` decorator to a
function that accepts a single `Blackbox.Inputs` argument and returns either a `Trace` or a `Result`
value. The size of the time step can be customized using the `step_size` decorator parameter.

The ``Blackbox.Inputs`` class has 2 attributes: ``static`` and ``times``. The ``static`` attribute
is a dictionary with the names of the static inputs as keys. The ``times`` attribute is a dictionary
where the keys are the signal evaluation times, and each value is a dictionary where the keys are
the signal names and the values are the signal value for the given time. If no signal inputs are
provided then the ``times`` dictionary will be empty.
::

    @models.blackbox(step_size=0.1)
    def blackbox(inputs: models.Blackbox.Inputs) -> models.Trace[float]:
        ...

ODEs
----

For systems that can be represented using ordinary differential equations, the `Ode` model can be
constructed using the `ode()` decorator from a function that accepts an `Ode.Inputs` argument and
returns a dictionary of values representing the derivative of each state variable. Systems are
simulated by integrating the derivative returned by the ODE using the method specificed with the
decorator ``method`` parameter.

The ``Ode.Inputs`` class contains 3 attributes: ``time``, ``static``, and ``signals``. ``time`` is
the current time from the integrator, ``static`` is a dictionary containing the variable names and
values of the system state at the current time, and ``static`` is a dictionary containing the signal
names and values for the current time.
::

    @models.ode(method="RK45")
    def ode(inputs: models.Ode.Inputs) -> dict[str, float]:
        ...
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Iterator, Mapping
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

T = TypeVar("T", bound=SupportsFloat)


class Trace(Generic[S], Iterable[tuple[float, S]]):
    """A time-annotated set of system states.

    This class can be iterated over to access each time, state pair in time-ascending order. This
    class can also be indexed by time to access a specific state. The `times` property iterates
    over the times in the trace, and the `states` iterates over the states. Both properties also
    iterate in time-ascending order.

    :param times: The times values for each state or the time-state mapping
    :param states: The states of the system if not using a time-state mapping
    :raises ValueError: If the length of `times` and `states` is not equal
    :raises ValueError: If not using a time-state mapping and states is omitted
    """

    @overload
    def __init__(self, elements: Mapping[T, S], /):
        ...

    @overload
    def __init__(self, *, times: Iterable[T], states: Iterable[S]):
        ...

    def __init__(
        self,
        times: Mapping[T, S] | Iterable[T],
        states: Iterable[S] | None = None,
    ):
        if isinstance(times, Mapping):
            self.elements = SortedDict({float(time): state for time, state in times.items()})
        else:
            if states is None:
                raise ValueError("must provide states with times")

            self.elements = SortedDict({float(time): state for time, state in zip(times, states)})

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
    def times(self) -> Iterable[float]:
        """An iterator over the times of the trace in time-ascending order."""

        return self.elements.keys()

    @property
    def states(self) -> Iterable[S]:
        """An iterator over the states of the trace in time-ascending order."""

        return self.elements.values()


class Result(Generic[S, E], _Result[Trace[S], E]):
    """Specialized version of `staliro.Result` that constructs a `Trace` as the value.

    :param states: The states of the system, either as a list or a dictionary where the keys are the associated times
    :param extra: The user annotation data for the result
    :param times: The times associated with each state if the states are provided as a list
    """

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

            trace = Trace(states=states, times=times)

        super().__init__(trace, extra)


class Model(Generic[S, E], ABC):
    """Representation of the simulation logic for the system under test (SUT)."""

    @abstractmethod
    def simulate(self, sample: Sample) -> _Result[Trace[S], E]:
        """Simulate a system and return a `staliro.Result` containing a `Trace`.

        :param sample: The sample containing the system inputs
        :returns: A result containing the ``Trace`` of system states and additional annotation data
        """


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
    def __call__(self, func: Callable[[Sample], _Result[Trace[S], E]]) -> ModelWrapper[S, E]:
        ...

    @overload
    def __call__(self, func: Callable[[Sample], Trace[R]]) -> ModelWrapper[R, None]:
        ...

    def __call__(self, func: ModelFunc[S, E, R]) -> ModelWrapper[S, E] | ModelWrapper[R, None]:
        return ModelWrapper(FuncWrapper(func))


@overload
def model(func: Callable[[Sample], _Result[Trace[S], E]]) -> ModelWrapper[S, E]:
    ...


@overload
def model(func: Callable[[Sample], Trace[R]]) -> ModelWrapper[R, None]:
    ...


@overload
def model(func: None = ...) -> ModelDecorator:
    ...


def model(
    func: ModelFunc[S, E, R] | None = None,
) -> ModelWrapper[S, E] | ModelWrapper[R, None] | ModelDecorator:
    """Create an `Model` from a function.

    The function provided to this model must accept a `Sample` value and return either a
    `Trace` value or a `staliro.Result` containing a ``Trace`` and additional annotation data. If no
    function is provided a decorator is returned, which can be called with the function instead.

    :param func: The function representing the system
    :returns: A ``Model`` or a decorator to create a ``Model``
    """

    decorator = ModelDecorator()

    if func:
        return decorator(func)

    return decorator


class Blackbox(Model[S, E]):
    """General system model which does not make assumptions about the underlying system.

    :param func: User-defined function to evaluate given ``Blackbox.Inputs`` into a `Trace`
                 or `staliro.Result`
    :param step_size: Time-step to use for interpolating signal values over the simulation interval
    """

    @frozen(slots=True)
    class Inputs:
        """Interpolated inputs to a Blackbox model.

        The times attributes will always contain as keys all of the interpolation times for the
        given ``tspan`` in the `TestOptions`. If no ``signals`` are defined in the ``TestOptions``,
        then the value for each time will be empty.

        :attribute static: The static (time-invariant) inputs to the system
        :attribute times: Mapping from each interpolation time to the values of each signal at that time
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
    def __call__(self, func: Callable[[Blackbox.Inputs], _Result[Trace[S], E]]) -> Blackbox[S, E]:
        ...

    @overload
    def __call__(self, func: Callable[[Blackbox.Inputs], Trace[R]]) -> Blackbox[R, None]:
        ...

    def __call__(self, func: BlackboxFunc[S, E, R]) -> Blackbox[S, E] | Blackbox[R, None]:
        return Blackbox(FuncWrapper(func), self.step_size)


@overload
def blackbox(
    func: Callable[[Blackbox.Inputs], _Result[Trace[S], E]],
    *,
    step_size: float = ...,
) -> Blackbox[S, E]:
    ...


@overload
def blackbox(
    func: Callable[[Blackbox.Inputs], Trace[R]],
    *,
    step_size: float = ...,
) -> Blackbox[R, None]:
    ...


@overload
def blackbox(func: None = ..., *, step_size: float = ...) -> BlackboxDecorator:
    ...


def blackbox(
    func: BlackboxFunc[S, E, R] | None = None,
    *,
    step_size: float = 0.1,
) -> Blackbox[S, E] | Blackbox[R, None] | BlackboxDecorator:
    """Create an `Blackbox` model from a function.

    The function provided to this model must accept a `Blackbox.Inputs` value and return either a
    `Trace` value or a `staliro.Result` containing a ``Trace`` and additional annotation data. If no
    function is provided a decorator is returned, which can be called with the function instead.
    The size of the time step for signal evaluation can be customized using the ``step_size``
    parameter.

    :param func: The function representing the system
    :param step_size: Size of the time step for signal evaluation
    :returns: A ``Blackbox`` model or a decorator to create a ``Blackbox``
    """

    decorator = BlackboxDecorator(step_size)

    if func:
        return decorator(func)

    return decorator


class Ode(Model[list[float], None]):
    """Model for systems that can be modeled by an Ordinary Differential Equation (ODE).

    This model is simulated by integration the state derivatives returned by the function. The
    integration method can be customized to provide different levels of fidelity. The default
    method is Runge-Kutta 4(5).

    :param func: User-defined function which is given a `Ode.Inputs` value and returns the
                 derivative of each state variable.
    :param method: The integration method for the ODE solver
    """

    Method: TypeAlias = Literal["RK45", "RK23", "DOP853", "Radau", "BDF", "LSODA"]

    @frozen(slots=True)
    class Inputs:
        """Set of inputs to an ODE model function.

        :attribute time: The current time of the integration
        :attribute state: Name-value map containing the state variables for the current time
        :attribute signals: Name-value map containing the signal values for the current time
        """

        time: float
        state: dict[str, float]
        signals: dict[str, float]

    def __init__(self, func: Callable[[Ode.Inputs], Mapping[str, float]], method: Ode.Method):
        self.func = func
        self.method = method

    def simulate(self, sample: Sample) -> Result[list[float], None]:
        if sample.signals.tspan is None:
            raise RuntimeError("ODE model requires tspan to be defined in TestOptions")

        names = list(sample.static)

        def integration_fn(time: float, state: NDArray[float_]) -> NDArray[float_]:
            static = {name: state[idx] for idx, name in enumerate(sample.static)}
            signals = {name: sample.signals[name].at_time(time) for name in sample.signals.names}
            derivs = self.func(Ode.Inputs(time, static, signals))

            return array([derivs[name] for name in names])

        integration = integrate.solve_ivp(
            fun=integration_fn,
            t_span=sample.signals.tspan,
            y0=[sample.static[name] for name in names],
            method=self.method,
        )

        return Result(
            times=integration.t.tolist(),
            states=integration.y.T.astype(dtype=float).tolist(),
            extra=None,
        )


class OdeDecorator:
    def __init__(self, method: Ode.Method):
        self.method = method

    def __call__(self, func: Callable[[Ode.Inputs], Mapping[str, float]]) -> Ode:
        return Ode(func, self.method)


@overload
def ode(
    func: Callable[[Ode.Inputs], Mapping[str, float]],
    *,
    method: Ode.Method = ...,
) -> Ode:
    ...


@overload
def ode(func: None = ..., *, method: Ode.Method = ...) -> OdeDecorator:
    pass


def ode(
    func: Callable[[Ode.Inputs], Mapping[str, float]] | None = None,
    *,
    method: Ode.Method = "RK45",
) -> Ode | OdeDecorator:
    """Create an `Ode` model from a function.

    The function provided to this model must accept a `Ode.Inputs` value and return a dictionary
    where each key is the name of a state variable the value is the derivative of that variable for
    the given time. If no function is provided a decorator is returned, which can be called with
    the function instead.

    :param func: The function representing the system ODE
    :param method: The integration method for the ODE solver.
                   Valid options are: ``["RK45", "RK23", "DOP853", "Radau", "BDF", "LSODA"]``
    :returns: An ``Ode`` model or a decorator to create an ``Ode`` model
    """

    decorator = OdeDecorator(method)

    if func:
        return decorator(func)

    return decorator
