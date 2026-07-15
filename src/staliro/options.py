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

import itertools
import random
from collections import OrderedDict
from collections.abc import Iterable, Mapping
from typing import TYPE_CHECKING, Any, Literal, TypeAlias

from attrs import Attribute, converters, define, field, validators
from numpy import float64, linspace
from numpy.typing import NDArray

from .cost_func import Inputs, Signals
from .optimizers import SampleT
from .signals import Interval, IntervalLike, Signal, SignalInput, UnboundInterval, _to_interval

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

    if isinstance(value, int) and value < 1:
        raise ValueError(f"{a.name} must be greater than 0")

    if isinstance(value, str) and value != "cores":
        raise ValueError(f"{a.name} only supports literal option 'cores'")


def _tspan(_: Any, a: AnyAttr, tspan: Interval) -> None:
    if tspan and tspan[0] >= tspan[1]:
        raise ValueError("Interval lower bound must be less than upper bound")


def _static_inputs(_: Any, a: AnyAttr, inputs: dict[str, Interval]) -> None:
    for interval in inputs.values():
        if interval[0] >= interval[1]:
            raise ValueError("Interval lower bound must be less than upper bound")

def _signals(_: Any, a: AnyAttr, signals: dict[str, SignalInput]) -> None:
    for signal in signals.values():
        if not isinstance(signal, SignalInput):
            raise TypeError("Signal inputs must be values of type SignalInput")


def _parse_static(values: Iterable[float], variables: Iterable[str]) -> dict[str, float]:
    return dict(zip(variables, values, strict=True))


_TSpan: TypeAlias = tuple[float, float]
_SignalInputs = dict[str, SignalInput]
_Signals = dict[str, Signal]


def _parse_signals(values: NDArray[float64], tspan: Interval, inputs: _SignalInputs) -> Signals:
    def _accumulate_idx(prev_idx: int, s_input: SignalInput) -> int:
        return prev_idx + len(s_input.control_points)

    idxs = itertools.accumulate(inputs.values(), _accumulate_idx, initial=0)
    idx_pairs = itertools.pairwise(idxs)

    def _create_signal(ipair: tuple[int, int], s_input: SignalInput) -> Signal:
        istart, istop = ipair
        control_values = values[istart:istop]

        if len(control_values) != len(s_input.control_points):
            raise ValueError("Incorrect number of points assigned to signal input")

        if isinstance(s_input.control_points, list):
            t_arr = linspace(
                start=tspan.start,
                stop=tspan.end,
                endpoint=False,
                num=len(control_values),
                dtype=float,
            )
            times: list[float] = t_arr.tolist()
        else:
            times = list(s_input.control_points.keys())

        return s_input.factory(times, control_values)

    signals = {
        name: _create_signal(ipair, s_input)
        for (name, s_input), ipair in zip(inputs.items(), idx_pairs, strict=True)
    }

    return Signals(signals, tspan)


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

    def intervals(self) -> list[Interval]:
        def _intervals() -> Iterable[Interval]:
            for name in self.static_inputs:
                yield self.static_inputs[name]

            for name in self.signals:
                control_points = self.signals[name].control_points

                if not isinstance(control_points, list):
                    control_points = control_points.values()

                yield from control_points

        return list(_intervals())

    def parse_sample(self, sample: SampleT) -> Inputs[SampleT]:
        if len(self.static_inputs) == 0 and len(self.signals) == 0:
            raise ValueError("Must provide at least one signal or static input")

        n_static = len(self.static_inputs)
        static = _parse_static(sample.values[:n_static], self.static_inputs)
        signals = _parse_signals(sample.values[n_static:], self.tspan, self.signals)

        return Inputs(sample, static, signals)
