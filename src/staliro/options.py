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

    def assign(self, x: NDArray[float64]) -> tuple[dict[str, float], dict[str, dict[float, float]]]:
        if len(self.static_inputs) == 0 and len(self.signals) == 0:
            raise ValueError("Must provide at least one signal or static input")

        values = array(x, dtype=float64)

        split_point = len(self.static_inputs)
        static_values, signal_values = split(values, [split_point])
        static = {
            name: cast(float, value)
            for name, value in zip(self.static_inputs.keys(), static_values, strict=True)
        }

        *signals, _ = self.signals.values()
        signal_split_points = accumulate(len(s.control_points) for s in signals)
        signal_groups = split(signal_values, list(signal_split_points))

        signals = {
            name: signal.assign(self.tspan, group)
            for (name, signal), group in zip(self.signals.items(), signal_groups, strict=True)
        }

        return static, signals

    def parse_sample(self, sample: SampleT) -> Inputs[SampleT]:
        static, signal_values = self.assign(sample.values)
        signals = {
            name: self.signals[name].factory(s.keys(), s.values())
            for name, s in signal_values.items()
        }

        return Inputs(sample, static, Signals(signals, self.tspan))
