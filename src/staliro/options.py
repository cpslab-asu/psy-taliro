from __future__ import annotations

import os
import random
from collections.abc import Mapping
from typing import TYPE_CHECKING, Literal

from attrs import Attribute, converters, define, field, validators
from typing_extensions import TypeAlias

from .signals import Interval, IntervalLike, SignalInput, _to_interval

if TYPE_CHECKING:
    AnyAttr: TypeAlias = Attribute[object]


def _seed_factory() -> int:
    return random.randint(0, 2**32 - 1)


def _to_static_inputs(inputs: Mapping[str, IntervalLike]) -> dict[str, Interval]:
    return {name: _to_interval(interval) for name, interval in inputs.items()}


def _to_signals(signals: Mapping[str, SignalInput]) -> dict[str, SignalInput]:
    return dict(signals)


class EmptyInterval:
    pass


@define(kw_only=True)
class TestOptions:
    """General options for controlling falsification behavior.

    Attributes:
        static_parameters: Parameters that will be provided to the system at the beginning and are
            time invariant (initial conditions)
        signals: System inputs that will vary over time
        seed: The initial seed of the random number generator
        iterations: The number of search iterations to perform in a run
        runs: The number times to run the optimizer
        interval: The time interval of the system simulation
        parallelization: Number of processes to use to parallelize runs of the optimizer. Acceptable
            values are: "cores" (all available cores), "all" (all runs), int (number of processes),
            None (no parallelization).
    """

    tspan: Interval | None = field(
        default=None,
        converter=converters.optional(_to_interval),
    )

    static_inputs: dict[str, Interval] = field(
        factory=dict,
        converter=_to_static_inputs,
    )

    signals: dict[str, SignalInput] = field(
        factory=dict,
        converter=_to_signals,
    )

    runs: int = field(default=1, validator=[validators.instance_of(int), validators.gt(0)])

    iterations: int = field(
        default=400,
        validator=[validators.instance_of(int), validators.gt(0)],
    )

    seed: int = field(
        factory=_seed_factory,
        validator=[validators.instance_of(int), validators.gt(0)],
    )

    parallelization: Literal["all", "cores"] | int | None = field(default=None)

    @tspan.validator
    def _tspan(self, _: AnyAttr, tspan: Interval) -> None:
        if tspan and tspan[0] >= tspan[1]:
            raise ValueError("Interval lower bound must be less than upper bound")

    @static_inputs.validator
    def _static_inputs(self, _: AnyAttr, inputs: dict[str, Interval]) -> None:
        for interval in inputs.values():
            if interval[0] >= interval[1]:
                raise ValueError("Interval lower bound must be less than upper bound")

    @signals.validator
    def _signals(self, _: AnyAttr, signals: dict[str, SignalInput]) -> None:
        for signal in signals.values():
            if not isinstance(signal, SignalInput):
                raise TypeError("Signal inputs must be values of type SignalInput")

        if len(signals) > 0 and not self.tspan:
            raise ValueError("Must define tspan if signal inputs are present")

    @parallelization.validator
    def _parallelization(self, _: AnyAttr, p: Literal["all", "cores"] | int | None) -> None:
        if isinstance(p, int) and p < 1:
            raise ValueError("Parallelization must be <= 1")

        if isinstance(p, str) and p != "all" and p != "cores":
            raise ValueError("Only 'all' and 'cores' are supported parallelization options")

    @property
    def processes(self) -> int | None:
        if self.parallelization == "all":
            return self.runs

        if self.parallelization == "cores":
            return os.cpu_count()

        return self.parallelization
