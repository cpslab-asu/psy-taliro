"""
Evaluate `Sample` values into cost values.

The cost function can be seen as a mapping from a `Sample` into a cost value. The intention is to
produce the values that will be used by the `Optimizer` to select new samples from the input space.
Therefore, each cost value should be some measure of the "quality" of the sample such that
minimizing or maximizing the cost will result in worse/better samples being selected.

Cost functions can be created by either sub-classing the `CostFunc` class or decorating a function
with the `costfunc` decorator.

Examples
--------

.. code-block:: python

    import staliro

    class Func(staliro.CostFunc[float, None]):
        def evaluate(self, sample: staliro.Sample) -> staliro.Result[C, E]:
            ...

    @staliro.costfunc()
    def func(sample: staliro.Sample) -> staliro.Result[C, E]:
        ...
"""

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
    """A result value containing additional annotation data.

    This class is parameterized by the type variables ``C`` and ``E``, which represent the type of
    the value and the type of the annotation data respectively.

    :param value: The result value
    :param extra: The annotation data value
    """

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
    """Signal inputs to the system.

    This object can be iterated over to access all `Signal` values, or indexed using the signal
    names.

    :param values: The values generated by the optimizer to create the signals
    :param opts: The test options containing the signal configurations
    """

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
        """Iterate over the names of the signals."""

        return self._signals.keys()

    @property
    def tspan(self) -> tuple[float, float] | None:
        """The interval of times over which all signals can be evaluated."""

        return self._tspan


SampleLike: TypeAlias = Union[Iterable[float], NDArray[Any]]


class Sample:
    """The set of static and signal inputs to the system.

    A sample is constructed from the raw vector of floats generated by the
    `Optimizer`, along with the test options. The options object is used to decompose the vector
    into the static inputs and the control points for each signal, which are used to construct each
    `Signal` input.

    :param values: vector of floating point values
    :param opts: The options provided to the test
    """

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
        """The raw numeric values received from the `Optimizer`."""

        return list(self._values)

    @property
    def static(self) -> OrderedDict[str, float]:
        """The static inputs to the system as defined in the `TestOptions`."""

        return self._static

    @property
    def signals(self) -> Signals:
        """The signal inputs to the system as defined by in the `TestOptions`."""

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
    ) -> Result[C, E]: ...

    @overload
    def __call__(self: FuncWrapper[P, R], *args: P.args, **kwargs: P.kwargs) -> Result[R, None]: ...

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
def wrap_func(func: Callable[P, Result[C, E]]) -> Callable[P, Result[C, E]]: ...


@overload
def wrap_func(func: Callable[P, R]) -> Callable[P, Result[R, None]]: ...


def wrap_func(func: Callable[P, Result[C, E] | R]) -> Callable[P, Result[C, E] | Result[R, None]]:
    return FuncWrapper(func)


class CostFunc(Generic[C, E], ABC):
    """The transformation from a `Sample` to a cost value.

    This class is parameterized by two type variables, ``C`` and ``E``. ``C`` is the type of the
    cost returned by this class and the ``value`` attribute in `Result` return value. ``E`` is the
    type of the annotation data in the ``extra`` attribute of the return value.
    """

    @abstractmethod
    def evaluate(self, sample: Sample) -> Result[C, E]:
        """Evaluate the given `Sample` into a cost value.

        :param sample: The sample to evaluate
        :returns: The cost value associated with the sample and any provided annotation data
        """


class Wrapper(CostFunc[C, E]):
    """Wrapper to transform a raw python function into a `CostFunc`.

    :param func: The user function to wrap
    """

    def __init__(self, func: Callable[[Sample], Result[C, E]]):
        self.func = func

    def evaluate(self, sample: Sample) -> Result[C, E]:
        """Apply the provided function to evaluate the given `Sample`.

        :param sample: The sample to evaluate with the user function
        :returns: The cost value associated with the sample and any provided annotation data
        """

        return self.func(sample)


class Decorator:
    """Function decorator to create a function :py:class:`Wrapper`."""

    @overload
    def __call__(self, func: Callable[[Sample], Result[C, E]]) -> Wrapper[C, E]: ...

    @overload
    def __call__(self, func: Callable[[Sample], R]) -> Wrapper[R, None]: ...

    def __call__(
        self, func: Callable[[Sample], Result[C, E] | R]
    ) -> Wrapper[C, E] | Wrapper[C, None]:
        """Create a :py:class:`Wrapper` from a Python function.

        Before creating the ``Wrapper`` instance, the function is wrapped to ensure that it will
        return a :py:class:`Result` value.

        :param func: The Python function to decorate
        :returns: A :py:class:`CostFunc` implementation using the provided function
        """

        return Wrapper(FuncWrapper(func))


@overload
def costfunc(func: Callable[[Sample], Result[C, E]]) -> Wrapper[C, E]: ...


@overload
def costfunc(func: Callable[[Sample], C]) -> Wrapper[C, None]: ...


@overload
def costfunc(func: None = ...) -> Decorator: ...


def costfunc(
    func: Callable[[Sample], Result[C, E]] | Callable[[Sample], R] | None = None,
) -> Wrapper[C, E] | Wrapper[R, None] | Decorator:
    """Transform a python function into a `CostFunc`.

    If the provided function returns any value other than a `Result`, the value will
    be wrapped in a ``Result`` with the ``extra`` field set to ``None``. This decorator can be
    called with or without parentheses.

    :param func: The function to transform
    :returns: A cost function or a decorator
    """

    decorator = Decorator()

    if func:
        return decorator(func)

    return decorator
