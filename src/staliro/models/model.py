from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator, Mapping
from typing import Generic, Protocol, TypeVar, Union, cast, overload

from sortedcontainers import SortedDict
from typing_extensions import TypeAlias

from ..cost_func import Result, Sample

S = TypeVar("S", covariant=True)
E = TypeVar("E", covariant=True)


class Trace(Generic[S], Iterable[tuple[float, S]]):
    @overload
    def __init__(self, times: Iterable[float], states: Iterable[S]):
        ...

    @overload
    def __init__(self, times: Mapping[float, S]):
        ...

    def __init__(
        self,
        times: Iterable[float] | Mapping[float, S],
        states: Iterable[S] | None = None,
    ):
        if isinstance(times, Mapping) and states is None:
            self.elements = SortedDict(times)
        elif isinstance(states, Iterable):
            self.elements = SortedDict(zip(times, states))
        else:
            raise TypeError("Trace accepts either two iterable, or a single mapping")

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


class Model(Generic[S, E], ABC):
    """Representation of the system under test (SUT)."""

    @abstractmethod
    def simulate(self, sample: Sample) -> Result[Trace[S], E]:
        ...


class UserResultFunc(Protocol[S, E]):
    def __call__(self, __sample: Sample) -> Result[Trace[S], E]:
        ...


class UserTraceFunc(Protocol[S]):
    def __call__(self, __sample: Sample) -> Trace[S]:
        ...


class UserModel(Model[S, Union[E, None]]):
    def __init__(self, func: UserResultFunc[S, E] | UserTraceFunc[S]):
        self.func = func

    def simulate(self, sample: Sample) -> Result[Trace[S], E | None]:
        result = self.func(sample)

        if isinstance(result, Trace):
            return Result(result, None)

        if isinstance(result, Result):
            return result

        raise TypeError("Model must return Trace or Result")


class Decorator(Protocol):
    @overload
    def __call__(self, __f: UserResultFunc[S, E]) -> UserModel[S, E]:
        ...

    @overload
    def __call__(self, __f: UserTraceFunc[S]) -> UserModel[S, None]:
        ...


T = TypeVar("T", covariant=True)
U = TypeVar("U", covariant=True)

UserFunc: TypeAlias = Union[UserResultFunc[S, E], UserTraceFunc[S]]


@overload
def model(func: UserResultFunc[S, E]) -> UserModel[S, E]:
    ...


@overload
def model(func: UserTraceFunc[S]) -> UserModel[S, None]:
    ...


@overload
def model(func: None = ...) -> Decorator:
    ...


def model(func: UserFunc[S, E] | None = None) -> UserModel[S, E | None] | Decorator:
    @overload
    def _decorator(func: UserResultFunc[T, U]) -> UserModel[T, U]:
        ...

    @overload
    def _decorator(func: UserTraceFunc[T]) -> UserModel[T, None]:
        ...

    def _decorator(func: UserFunc[T, U]) -> UserModel[T, U | None]:
        return UserModel(func)


    return _decorator(func) if func else _decorator


__all__ = ["Trace", "Model", "model"]
