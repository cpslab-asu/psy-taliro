from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Mapping

import attrs
import typing_extensions

from .cost_func import CostFunc, Result
from .models import Blackbox, Model, Ode, Trace
from .optimizers import Sample
from .specifications import Specification

P = typing_extensions.ParamSpec("P")
T = typing_extensions.TypeVar("T")
E = typing_extensions.TypeVar("E", default=None)


def ensure_result(value: Result[T, E] | T) -> Result[T, E | None]:
    if isinstance(value, Result):
        return typing.cast(Result[T, E], value)

    return Result(typing.cast(T, value), None)


@attrs.define()
class UserCostFunc(CostFunc[T, E]):
    f: Callable[[Sample], Result[T, E]]

    @typing_extensions.override
    def evaluate(self, sample: Sample) -> Result[T, E]:
        return self.f(sample)


@typing_extensions.overload
def costfunc(f: Callable[[Sample], Result[T, E]]) -> CostFunc[T, E]:  # type: ignore[overload-overlap] # pyright: ignore[reportOverlappingOverload],
    ...


@typing_extensions.overload
def costfunc(f: Callable[[Sample], T]) -> CostFunc[T, None]: ...


def costfunc(f: Callable[[Sample], Result[T, E] | T]) -> CostFunc[T, E | None]:
    """Transform a python function into a `CostFunc`.

    If the provided function returns any value other than a `Result`, the value will
    be wrapped in a ``Result`` with the ``extra`` field set to ``None``. This decorator can be
    called with or without parentheses.

    :param f: The function to transform
    :returns: A cost function implementation wrapping the provided function
    """

    return UserCostFunc(lambda s: ensure_result(f(s)))


@attrs.define()
class UserModel(Model[T, E]):
    f: Callable[[Sample], Result[Trace[T], E]]

    @typing_extensions.override
    def simulate(self, sample: Sample) -> Result[Trace[T], E]:
        return self.f(sample)


@typing_extensions.overload
def model(f: Callable[[Sample], Trace[T]]) -> Model[T, None]: ...


@typing_extensions.overload
def model(f: Callable[[Sample], Result[Trace[T], E]]) -> Model[T, E]: ...


def model(f: Callable[[Sample], Trace[T] | Result[Trace[T], E]]) -> Model[T, E | None]:
    """Create an `Model` from a function.

    The function provided to this model must accept a `Sample` value and return either a
    `Trace` value or a `staliro.Result` containing a ``Trace`` and additional annotation data.

    :param f: The function representing the system
    :returns: A ``Model`` implementation wrapping the provided function
    """

    return UserModel(lambda s: ensure_result(f(s)))


@attrs.define()
class BlackboxDecorator:
    step_size: float

    @typing_extensions.overload
    def __call__(self, f: Callable[[Blackbox.Inputs], Trace[T]]) -> Blackbox[T, None]: ...

    @typing_extensions.overload
    def __call__(self, f: Callable[[Blackbox.Inputs], Result[Trace[T], E]]) -> Blackbox[T, E]: ...

    def __call__(
        self, f: Callable[[Blackbox.Inputs], Trace[T] | Result[Trace[T], E]]
    ) -> Blackbox[T, E | None]:
        return Blackbox(lambda x: ensure_result(f(x)), self.step_size)


def blackbox(*, step_size: float) -> BlackboxDecorator:
    """Create an `Blackbox` model from a function.

    The function provided to this model must accept a `Blackbox.Inputs` value and return either a
    `Trace` value or a `staliro.Result` containing a ``Trace`` and additional annotation data. If no
    function is provided a decorator is returned, which can be called with the function instead.
    The size of the time step for signal evaluation can be customized using the ``step_size``
    parameter.

    :param step_size: Size of the time step for signal evaluation
    :returns: A decorator to wrap a function into a ``Blackbox`` model implementation
    """

    return BlackboxDecorator(step_size)


if typing.TYPE_CHECKING:
    OdeFunc: typing_extensions.TypeAlias = Callable[[Ode.Inputs], Mapping[str, float]]


def ode(method: Ode.Method) -> Callable[[OdeFunc], Ode]:
    """Create an `Ode` model from a function.

    This function sets the integration method for the ODE model and returns a
    decorator to wrap a function into an ODE implementation. The function
    provided to the returned decorator must accept a `Ode.Inputs` value and
    return a dictionary where each key is the name of a state variable the value
    is the derivative of that variable for the given time.

    :param method: The integration method for the ODE solver.
                   Valid options are: ``["RK45", "RK23", "DOP853", "Radau", "BDF", "LSODA"]``
    :returns: A decorator to create an ``Ode`` model implementation wrapping the provided function
    """

    def _decorator(f: OdeFunc) -> Ode:
        return Ode(f, method)

    return _decorator


C = typing_extensions.TypeVar("C")


@attrs.define()
class UserSpecification(Specification[T, C, E]):
    f: Callable[[Trace[T]], Result[C, E]]

    @typing_extensions.override
    def evaluate(self, trace: Trace[T]) -> Result[C, E]:
        return self.f(trace)


@typing_extensions.overload
def specification(f: Callable[[Trace[T]], Result[C, E]]) -> Specification[T, C, E]: ...  # type: ignore[overload-overlap]


@typing_extensions.overload
def specification(f: Callable[[Trace[T]], C]) -> Specification[T, C, None]: ...


def specification(f: Callable[[Trace[T]], Result[C, E] | C]) -> Specification[T, C, E | None]:
    """Create a specification from a function.

    The function must accept a `Trace` as an argument and return either a cost
    value or a `staliro.Result` containing the cost value and additional
    annotation data. If only a cost value is returned, a ``staliro.Result`` will
    be constructed with the annotation set to ``None``.

    :param func: The function to use to construct the specification
    :returns: A `Specification` implementation wrapping the provided function
    """

    return UserSpecification(lambda s: ensure_result(f(s)))
