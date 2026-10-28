"""
Definitions for the options that can be used to customize the testing behavior.

Behavior customization is accomplished through the `TestObject` class, which must
be provided as an argument to either the `staliro` or `setup` functions.

Examples
--------

.. code-block:: python

    import staliro

    options = staliro.TestOptions(
        runs = 10,
        iterations = 450,
        static_inputs={
            "speed": (0, 100),
            "fuel": [0, 255],
        },
    )
"""

from __future__ import annotations

import random
import warnings
from collections import OrderedDict
from collections.abc import Iterable, Mapping
from itertools import accumulate
from typing import TYPE_CHECKING, Any, Literal, TypeAlias, cast

from attrs import Attribute, converters, define, field, validators
from numpy import array, float64, split
from numpy.typing import NDArray

from .cost_func import Inputs, Signals
from .optimizers import SampleT
from .signals import Interval, IntervalLike, SignalInput, UnboundInterval, _to_interval

if TYPE_CHECKING:
    AnyAttr: TypeAlias = Attribute[Any]


def _seed_factory() -> int:
    return random.randint(0, 2**32 - 1)


def _to_static_inputs(inputs: Mapping[str, IntervalLike]) -> OrderedDict[str, Interval]:
    return OrderedDict({name: _to_interval(interval) for name, interval in inputs.items()})


def _to_signals(signals: Mapping[str, SignalInput]) -> OrderedDict[str, SignalInput]:
    return OrderedDict(signals)


def _parallelization(_: Any, a: AnyAttr, value: Literal["cores"] | int | None) -> None:
    if value is None:
        return

    if isinstance(value, int):
        if value < 1:
            raise ValueError(f"{a.name} must be greater than 0")

        if value == 1:
            warnings.warn(
                f"Setting {a.name} to 1 will create a worker pool with only a single worker, "
                "which will not improve performance and is probably not the intended configuration."
                f"Leave {a.name} unset or set to None to avoid this problem.",
                stacklevel=2,
            )

    if isinstance(value, str) and value != "cores":
        raise ValueError(f"{a.name} only supports literal option 'cores'")


def _tspan(_: Any, a: AnyAttr, tspan: Interval) -> None:
    if tspan.start >= tspan.end:
        raise ValueError("Interval lower bound must be less than upper bound")


def _static_inputs(_: Any, a: AnyAttr, inputs: dict[str, Interval]) -> None:
    for interval in inputs.values():
        if interval.start >= interval.end:
            raise ValueError("Interval lower bound must be less than upper bound")


def _signals(_: Any, a: AnyAttr, signals: dict[str, SignalInput]) -> None:
    for signal in signals.values():
        if not isinstance(signal, SignalInput):
            raise TypeError("Signal inputs must be values of type SignalInput")


def _assign_static(static_inputs: Mapping[str, Interval], x: NDArray[float64]) -> dict[str, float]:
    return {
        name: cast(float, value)
        for name, value in zip(static_inputs.keys(), x, strict=True)
    }


def _assign_signals(
    signals: Mapping[str, SignalInput],
    tspan: Interval,
    x: NDArray[float64],
) -> dict[str, dict[float, float]]:
    *inputs, _ = signals.values()
    signal_split_points = accumulate(len(i.control_points) for i in inputs)
    signal_groups = split(x, list(signal_split_points))

    return {
        name: signal.assign(tspan, group)
        for (name, signal), group in zip(signals.items(), signal_groups, strict=True)
    }


@define(kw_only=True)
class TestOptions:
    """General options for controlling falsification behavior.

    :param tspan: The time interval for testing
    :param static_inputs: Parameters that will be provided to the system at the beginning and are time invariant (initial conditions).
    :param signals: System inputs that will vary over time
    :param seed: The initial seed of the random number generator
    :param iterations: The number of search iterations to perform in a run
    :param runs: The number times to run the optimizer
    :param processes: Number of processes to use to parallelize sample evaluation
    :param threads: Number of threads to use to parallelize sample evaluation
    """

    tspan: Interval = field(
        factory=UnboundInterval,
        converter=converters.optional(_to_interval),
        validator=_tspan,
    )

    # We use an ordered dict to guarantee keys will be iterated in the same order every time
    static_inputs: OrderedDict[str, Interval] = field(
        factory=OrderedDict,
        converter=_to_static_inputs,
        validator=_static_inputs,
    )

    signals: OrderedDict[str, SignalInput] = field(
        factory=OrderedDict,
        converter=_to_signals,
        validator=_signals,
    )

    runs: int = field(
        default=1,
        validator=[validators.instance_of(int), validators.gt(0)],
    )

    iterations: int = field(
        default=400,
        validator=[validators.instance_of(int), validators.gt(0)],
    )

    seed: int = field(
        factory=_seed_factory,
        validator=[validators.instance_of(int), validators.gt(0)],
    )

    processes: Literal["cores"] | int | None = field(
        default=None,
        validator=_parallelization,
    )

    threads: Literal["cores"] | int | None = field(
        default=None,
        validator=_parallelization,
    )

    def intervals(self) -> Iterable[Interval]:
        yield from self.static_inputs.values()

        for signal in self.signals.values():
            yield from signal.intervals()

    def assign_static(self, x: NDArray[float64]) -> dict[str, float]:
        """Assign each static input variable to its value in the given sample.

        Args:
            sample: The sequence of values to generate an assignment for

        Returns:
            A dictionary where each key is the name of a static input variable, and each value is
            the value of that variable from the input vector.

        Raises:
            ValueError: If the number of values in the sample is less than the number of static
                        inputs specified in the `TestOptions`.
        """

        return _assign_static(self.static_inputs, x[:len(self.static_inputs)])

    def assign_signals(self, x: NDArray[float64]) -> dict[str, dict[float, float]]:
        """Assign each signal input its control point values in the given sample.

        Args:
            sample: The sequence of values to generate an assignment for

        Returns:
            A dictionary where each key is the name of a signal input, and each value is dictionary.
            Each sub-dictionary contains the time value for each control point as the keys, and the
            value of each control point as the mapped value.

        Raises:
            ValueError: If the number of values in the sample is less than the number of control
                        points specified across all signals in the `TestOptions`.
        """

        return _assign_signals(self.signals, self.tspan, x[len(self.static_inputs):])

    def assign(self, x: NDArray[float64]) -> tuple[dict[str, float], dict[str, dict[float, float]]]:
        """Assign each value in the given sample to its associated variable or signal.

        The static variables are represented as a dictionary, where each variable name is associated
        with its corresponding value. The signals are represented with nested dictionaries, where
        the outer dictionary associates the signal name to an inner dictionary representing the set
        of control points for the signal. The control point dictionary keys represent time values
        and the dictionary values represent the signal control point value for the given time.

        Args:
            sample: The sequence of values to generate an assignment for

        Returns:
            A tuple where the first element contains the static variable assignments and the second
            element contains the signal variable assignments.

        Raises:
            ValueError: If the number of values in the sample does not match the number of inputs
                        specified in the `TestOptions`.
        """

        if len(self.static_inputs) == 0 and len(self.signals) == 0:
            raise ValueError("Must provide at least one signal or static input")

        split_pt = len(self.static_inputs)
        static, signals = split(x, [split_pt])

        return (
            _assign_static(self.static_inputs, static),
            _assign_signals(self.signals, self.tspan, signals),
        )

    def parse_sample(self, sample: SampleT) -> Inputs[SampleT]:
        static, signal_values = self.assign(sample.values)
        signals = {
            name: self.signals[name].factory(s.keys(), s.values())
            for name, s in signal_values.items()
        }

        return Inputs(sample, static, Signals(signals, self.tspan))
