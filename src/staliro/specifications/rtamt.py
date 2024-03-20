from __future__ import annotations

from collections.abc import Sequence
from typing import Union, cast, overload

from rtamt import StlDenseTimeSpecification, StlDiscreteTimeSpecification
from typing_extensions import TypeAlias

from ..cost_func import Result
from ..models import Trace
from .specification import Specification

_Times: TypeAlias = list[float]
_States: TypeAlias = dict[str, list[float]]


@overload
def _parse_trace(trace: Trace[dict[str, float]]) -> tuple[_Times, _States]:
    ...


@overload
def _parse_trace(trace: Trace[Sequence[float]], columns: dict[str, int]) -> tuple[_Times, _States]:
    ...


def _parse_trace(
    trace: Trace[dict[str, float]] | Trace[Sequence[float]],
    columns: dict[str, int] | None = None,
) -> tuple[_Times, _States]:
    times = list(trace.times)
    states = {}

    if columns:
        seq_trace = cast(Trace[Sequence[float]], trace)

        for name, column in columns.items():
            states[name] = [s[column] for s in seq_trace.states]
    else:
        dict_trace = cast(Trace[dict[str, float]], trace)
        state = dict_trace[times[0]]

        for name in state:
            states[name] = [s[name] for s in dict_trace.states]

    return times, states


def _evaluate_discrete(formula: str, times: list[float], states: dict[str, list[float]]) -> float:
    try:
        period = times[1] - times[0]
    except IndexError as e:
        raise ValueError("trace must have at least two states to be evaluated") from e

    spec = StlDiscreteTimeSpecification()
    spec.spec = formula

    for name in states:
        spec.declare_var(name, "float")

    spec.set_sampling_period(round(period, 2), "s", 0.1)
    spec.parse()

    robustness = spec.evaluate({"time": times, **states})
    return robustness[0][1]


class DiscreteMapped(Specification[Sequence[float], float, None]):
    def __init__(self, requirement: str, columns: dict[str, int]):
        self.requirement = requirement
        self.columns = columns

    def evaluate(self, trace: Trace[Sequence[float]]) -> Result[float, None]:
        times, states = _parse_trace(trace, self.columns)
        cost = _evaluate_discrete(self.requirement, times, states)

        return Result(cost, None)


class DiscreteNamed(Specification[dict[str, float], float, None]):
    def __init__(self, requirement: str):
        self.requirement = requirement

    def evaluate(self, trace: Trace[dict[str, float]]) -> Result[float, None]:
        times, states = _parse_trace(trace)
        cost = _evaluate_discrete(self.requirement, times, states)

        return Result(cost, None)


Discrete: TypeAlias = Union[DiscreteMapped, DiscreteNamed]


@overload
def parse_discrete(formula: str, columns: dict[str, int]) -> DiscreteMapped:
    ...


@overload
def parse_discrete(formula: str, columns: None = ...) -> DiscreteNamed:
    ...


def parse_discrete(formula: str, columns: dict[str, int] | None = None) -> Discrete:
    if columns:
        return DiscreteMapped(formula, columns)

    return DiscreteNamed(formula)


def _evaluate_dense(phi: str, times: list[float], states: dict[str, list[float]]) -> float:
    spec = StlDenseTimeSpecification()
    spec.spec = phi

    for name in states:
        spec.declare_var(name, "float")

    spec.parse()

    traces = [(name, list(zip(times, states[name]))) for name in states]
    robustness = spec.evaluate(*traces)

    return robustness[0][1]


class DenseMapped(Specification[Sequence[float], float, None]):
    def __init__(self, requirement: str, columns: dict[str, int]):
        self.requirement = requirement
        self.columns = columns

    def evaluate(self, trace: Trace[Sequence[float]]) -> Result[float, None]:
        times, states = _parse_trace(trace, self.columns)
        cost = _evaluate_dense(self.requirement, times, states)

        return Result(cost, None)


class DenseNamed(Specification[dict[str, float], float, None]):
    def __init__(self, requirement: str):
        self.requirement = requirement

    def evaluate(self, trace: Trace[dict[str, float]]) -> Result[float, None]:
        times, states = _parse_trace(trace)
        cost = _evaluate_dense(self.requirement, times, states)

        return Result(cost, None)


Dense: TypeAlias = Union[DenseMapped, DenseNamed]


@overload
def parse_dense(requirement: str, columns: dict[str, int]) -> DenseMapped:
    ...


@overload
def parse_dense(requirement: str, columns: None = ...) -> DenseNamed:
    ...


def parse_dense(requirement: str, columns: dict[str, int] | None = None) -> Dense:
    if columns:
        return DenseMapped(requirement, columns)

    return DenseNamed(requirement)


