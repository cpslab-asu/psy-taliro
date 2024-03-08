from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from collections.abc import Callable, Iterable, Iterator
from typing import Any, Generic, TypeVar, Union, overload

from attrs import frozen
from numpy import linspace, ndarray
from numpy.typing import NDArray
from typing_extensions import ParamSpec, TypeAlias

from .options import TestOptions
from .signals import Signal

C = TypeVar("C", covariant=True)
E = TypeVar("E", covariant=True)


@frozen(slots=True)
class Result(Generic[C, E]):
    value: C
    extra: E


def _parse_signals(values: list[float], opts: TestOptions) -> dict[str, Signal]:
    if len(opts.signals) == 0:
        return {}

    assert opts.tspan is not None
    tstart, tend = opts.tspan

    signals: dict[str, Signal] = {}
    signal_start = 0

    for name in opts.signals:
        signal = opts.signals[name]
        n_vals = len(signal.control_points)

        if isinstance(signal.control_points, list):
            times = linspace(tstart, tend, endpoint=False, num=n_vals, dtype=float)
            signal_times: list[float] = times.tolist()
        else:
            signal_times = list(signal.control_points.keys())

        signal_end = signal_start + n_vals
        signal_vals = values[signal_start:signal_end]
        signal_start = signal_end

        if len(signal_vals) != n_vals:
            raise ValueError("Not enough control points to create signal")

        signals[name] = signal.factory(signal_times, signal_vals)

    return signals


class Signals:
    def __init__(self, values: list[float], opts: TestOptions):
        self._tspan = opts.tspan
        self._signals = _parse_signals(values, opts)

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
    def tspan(self) -> tuple[float, float] | None:
        return self._tspan


SampleLike: TypeAlias = Union[Iterable[float], NDArray[Any]]


class Sample:
    def __init__(self, values: SampleLike, opts: TestOptions):
        if isinstance(values, ndarray):
            self._values: list[float] = values.astype(dtype=float).tolist()
        else:
            self._values = list(values)

        self._static = OrderedDict(
            {name: self._values[idx] for idx, name in enumerate(opts.static_inputs)}
        )

        self._signals = Signals(self._values[len(self._static) :], opts)

    @property
    def values(self) -> list[float]:
        return list(self._values)

    @property
    def static(self) -> OrderedDict[str, float]:
        return self._static

    @property
    def signals(self) -> Signals:
        return self._signals


P = ParamSpec("P")
R = TypeVar("R")


class FuncWrapper(Generic[P, R]):
    def __init__(self, func: Callable[P, R]):
        self.func = func

    @overload
    def __call__(
        self: FuncWrapper[P, Result[C, E]],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Result[C, E]:
        ...

    @overload
    def __call__(self: FuncWrapper[P, R], *args: P.args, **kwargs: P.kwargs) -> Result[R, None]:
        ...

    def __call__(
        self: FuncWrapper[P, Result[C, E] | R],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> Result[C, E] | Result[R, None]:
        retval = self.func(*args, **kwargs)

        if not isinstance(retval, Result):
            return Result(retval, None)

        return retval


@overload
def wrap_func(func: Callable[P, Result[C, E]]) -> Callable[P, Result[C, E]]:
    ...


@overload
def wrap_func(func: Callable[P, R]) -> Callable[P, Result[R, None]]:
    ...


def wrap_func(func: Callable[P, Result[C, E] | R]) -> Callable[P, Result[C, E] | Result[R, None]]:
    return FuncWrapper(func)


class CostFunc(Generic[C, E], ABC):
    @abstractmethod
    def evaluate(self, sample: Sample) -> Result[C, E]:
        ...


class Wrapper(CostFunc[C, E]):
    def __init__(self, func: Callable[[Sample], Result[C, E]]):
        self.func = func

    def evaluate(self, sample: Sample) -> Result[C, E]:
        return self.func(sample)


class Decorator:
    @overload
    def __call__(self, func: Callable[[Sample], Result[C, E]]) -> Wrapper[C, E]:
        ...

    @overload
    def __call__(self, func: Callable[[Sample], R]) -> Wrapper[R, None]:
        ...

    def __call__(
        self, func: Callable[[Sample], Result[C, E] | R]
    ) -> Wrapper[C, E] | Wrapper[C, None]:
        return Wrapper(FuncWrapper(func))


@overload
def costfunc(func: Callable[[Sample], Result[C, E]]) -> Wrapper[C, E]:
    ...


@overload
def costfunc(func: Callable[[Sample], C]) -> Wrapper[C, None]:
    ...


@overload
def costfunc(func: None = ...) -> Decorator:
    ...


def costfunc(
    func: Callable[[Sample], Result[C, E]] | Callable[[Sample], R] | None = None,
) -> Wrapper[C, E] | Wrapper[R, None] | Decorator:
    decorator = Decorator()

    if func:
        return decorator(func)

    return decorator
