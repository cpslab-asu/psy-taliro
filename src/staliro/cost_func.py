from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from typing import Any, Generic, Protocol, TypeVar, Union, overload

from attrs import define, frozen
from numpy import linspace, ndarray
from numpy.typing import NDArray
from typing_extensions import TypeAlias

from .options import TestOptions
from .signals import Signal

C = TypeVar("C", covariant=True)
E = TypeVar("E", covariant=True)


@frozen(slots=True)
class Result(Generic[C, E]):
    value: C
    extra: E


SampleLike: TypeAlias = Union[Iterable[float], NDArray[Any]]


def _parse_signals(values: list[float], order: list[str], opts: TestOptions) -> dict[str, Signal]:
    tstart, tend = opts.tspan
    signal_start = len(opts.static_parameters)
    signals = {}

    for name in order:
        signal_opts = opts.signals[name]
        n_vals = len(signal_opts.control_points)
        signal_times: list[float] = linspace(tstart, tend, num=n_vals, dtype=float).tolist()

        signal_end = signal_start + n_vals
        signal_vals = values[signal_start:signal_end]
        signal_start = signal_end

        if len(signal_vals) != n_vals:
            raise ValueError("Not enough control points to create signal")

        signals[name] = signal_opts.factory(signal_times, signal_vals)

    return signals


class Signals:
    def __init__(self, values: list[float], order: list[str], opts: TestOptions):
        self._tspan = opts.tspan
        self._signals = _parse_signals(values, order, opts)

    def __len__(self) -> int:
        return len(self._signals)

    def __iter__(self) -> Iterator[Signal]:
        return iter(self._signals.values())

    def __getitem__(self, name: str) -> Signal:
        return self._signals[name]

    @property
    def names(self) -> Iterable[str]:
        return self._signals.keys()

    @property
    def tspan(self) -> tuple[float, float]:
        return self._tspan


class Sample:
    @define()
    class Order:
        static: list[str]
        signals: list[str]

    def __init__(self, values: SampleLike, order: Sample.Order, opts: TestOptions):
        if isinstance(values, ndarray):
            self._values: list[float] = values.astype(dtype=float).tolist()
        else:
            self._values = list(values)

        self._static = {name: self._values[idx] for idx, name in enumerate(order.static)}
        self._signals = Signals(self._values, order.signals, opts)

    @property
    def values(self) -> list[float]:
        return list(self._values)

    @property
    def static(self) -> dict[str, float]:
        return self._static

    @property
    def signals(self) -> Signals:
        return self._signals


class CostFunc(Generic[C, E], ABC):
    @abstractmethod
    def evaluate(self, sample: Sample) -> Result[C, E]:
        ...


class UserResultFunc(Protocol[C, E]):
    def __call__(self, __sample: Sample) -> Result[C, E]:
        ...


class UserValueFunc(Protocol[C]):
    def __call__(self, __sample: Sample) -> C:
        ...


UserFunc: TypeAlias = Union[UserResultFunc[C, E], UserValueFunc[C]]


class UserCostFunc(CostFunc[C, Union[E, None]]):
    def __init__(self, func: UserFunc[C, E]):
        self.func = func

    def evaluate(self, sample: Sample) -> Result[C, E | None]:
        result = self.func(sample)

        if not isinstance(result, Result):
            return Result(result, None)

        return result


class Decorator(Protocol):
    @overload
    def __call__(self, func: UserResultFunc[C, E]) -> UserCostFunc[C, E]:
        ...

    @overload
    def __call__(self, func: UserValueFunc[C]) -> UserCostFunc[C, None]:
        ...


T = TypeVar("T", covariant=True)
U = TypeVar("U", covariant=True)


@overload
def costfunc(func: UserResultFunc[C, E]) -> UserCostFunc[C, E]:
    ...


@overload
def costfunc(func: UserValueFunc[C]) -> UserCostFunc[C, None]:
    ...


@overload
def costfunc(func: None = ...) -> Decorator:
    ...


def costfunc(func: UserFunc[C, E] | None = None) -> UserCostFunc[C, E | None] | Decorator:
    @overload
    def _decorator(func: UserResultFunc[T, U]) -> UserCostFunc[T, U]:
        ...

    @overload
    def _decorator(func: UserValueFunc[T]) -> UserCostFunc[T, None]:
        ...

    def _decorator(func: UserFunc[T, U]) -> UserCostFunc[T, U | None]:
        return UserCostFunc(func)

    return _decorator(func) if func else _decorator


__all__ = ["CostFunc", "Result", "Sample", "costfunc"]
