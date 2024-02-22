from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from typing import Generic, Protocol, TypeVar, cast, overload

from attrs import frozen

from ..options import Interval
from ..signals import Signal

S = TypeVar("S", covariant=True)
E = TypeVar("E",  covariant=True)


class Trace(Generic[S], Iterable[tuple[float, S]]):
    @overload
    def __init__(self, times: Iterable[float], states: Iterable[S]):
        ...

    @overload
    def __init__(self, times: Mapping[float, S]):
        ...

    def __init__(self, times: Iterable[float] | Mapping[float, S], states: Iterable[S] | None = None):
        if isinstance(times, Mapping) and states is None:
            self.elements = dict(times)
        elif isinstance(states, Iterable):
            self.elements = dict(zip(times, states))
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


@frozen()
class Inputs:
    static: Sequence[float]
    signals: Sequence[Signal]


class Model(Protocol[S, E]):
    def __call__(self, __inputs: Inputs, __interval: Interval) -> tuple[Trace[S], E]:
        ...


__all__ = ["Trace", "Inputs", "Model"]
