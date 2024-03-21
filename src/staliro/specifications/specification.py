from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Generic, TypeVar, overload

from ..cost_func import FuncWrapper, Result
from ..models import Trace

S = TypeVar("S", contravariant=True)
C = TypeVar("C", covariant=True)
E = TypeVar("E", covariant=True)
R = TypeVar("R", covariant=True)


class Specification(Generic[S, C, E], ABC):
    """Class that represents a requirement to be evaluated using simulation data.

    A specification should accept the trajectories and timestamps generated by a model and return
    a value which represents the "goodness" of the model results with respect to some criteria.
    """

    @abstractmethod
    def evaluate(self, __trace: Trace[S]) -> Result[C, E]:
        """Evaluate trajectories and timestamps with respect to some requirement.

        Args:
            trajectories: Matrix of states where each row represents a state variable.
            timestamps: Vector of time values corresponding to each column of the trajectories
                        matrix.

        Returns:
            A value indicating the "goodness" of the trajectories according to the requirement.
        """

        ...


class UserSpecification(Specification[S, C, E]):
    def __init__(self, func: Callable[[Trace[S]], Result[C, E]]):
        self.func = func

    def evaluate(self, trace: Trace[S]) -> Result[C, E]:
        return self.func(trace)


class Decorator:
    @overload
    def __call__(self, func: Callable[[Trace[S]], Result[C, E]]) -> UserSpecification[S, C, E]:
        ...

    @overload
    def __call__(self, func: Callable[[Trace[S]], R]) -> UserSpecification[S, R, None]:
        ...

    def __call__(
        self, func: Callable[[Trace[S]], Result[C, E]] | Callable[[Trace[S]], R]
    ) -> UserSpecification[S, C, E] | UserSpecification[S, R, None]:
        return UserSpecification(FuncWrapper(func))


@overload
def specification(func: Callable[[Trace[S]], Result[C, E]]) -> UserSpecification[S, C, E]:
    ...


@overload
def specification(func: Callable[[Trace[S]], R]) -> UserSpecification[S, R, None]:
    ...


@overload
def specification(func: None = ...) -> Decorator:
    ...


def specification(
    func: Callable[[Trace[S]], Result[C, E]] | Callable[[Trace[S]], R] | None = None,
) -> UserSpecification[S, C, E] | UserSpecification[S, R, None] | Decorator:
    """Create a specification from a function.

    If no function is provided, then a decorator is returned that can be called with the function
    to create the specification. The function must accept a `Trace` as an argument and return either
    a cost value or a `staliro.Result` containing the cost value and additional annotation data. If
    only a cost value is returned, a ``staliro.Result`` will be constructed with the annotation set
    to ``None``.

    :param func: The function to use to construct the specification
    :returns: A `Specification` or a a decorator to construct a ``Specification``
    """

    decorator = Decorator()

    if func:
        return decorator(func)

    return decorator
