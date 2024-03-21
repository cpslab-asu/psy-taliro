from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Union, cast, overload

from rtamt import StlDenseTimeSpecification, StlDiscreteTimeSpecification
from typing_extensions import TypeAlias

from ..cost_func import Result
from ..models import Trace
from .specification import Specification

_Times: TypeAlias = list[float]
_States: TypeAlias = dict[str, list[float]]


@overload
def _parse_trace(trace: Trace[dict[str, float]]) -> tuple[_Times, _States]: ...


@overload
def _parse_trace(
    trace: Trace[Sequence[float]], columns: dict[str, int]
) -> tuple[_Times, _States]: ...


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
    """A discrete-time STL specification using a variable-column map.

    The variable-column map is a mapping from the variable names in the formula to columns in the
    state, which is a vector. In addition, the trace used for evaluation must fulfill the following
    criteria:

    - There is an equal amount of time between each state in the trace
    - There are at least two states in the trace

    :param requirement: The formula to evaluate using the `Trace`
    :param columns: A mapping from variables names to columns of the state vector
    """

    def __init__(self, requirement: str, columns: dict[str, int]):
        self.requirement = requirement
        self.columns = columns

    def evaluate(self, trace: Trace[Sequence[float]]) -> Result[float, None]:
        times, states = _parse_trace(trace, self.columns)
        cost = _evaluate_discrete(self.requirement, times, states)

        return Result(cost, None)


class DiscreteNamed(Specification[dict[str, float], float, None]):
    """A discrete-time STL specification using the variable names in the state.

    The trace used for evaluation must fulfill the following criteria:

    - There is an equal amount of time between each state in the trace
    - There are at least two states in the trace

    :param requirement: The formula to evaluate using the `Trace`
    """

    def __init__(self, requirement: str):
        self.requirement = requirement

    def evaluate(self, trace: Trace[dict[str, float]]) -> Result[float, None]:
        times, states = _parse_trace(trace)
        cost = _evaluate_discrete(self.requirement, times, states)

        return Result(cost, None)


Discrete: TypeAlias = Union[DiscreteMapped, DiscreteNamed]


@overload
def parse_discrete(formula: str, columns: Mapping[str, int]) -> DiscreteMapped: ...


@overload
def parse_discrete(formula: str, columns: None = ...) -> DiscreteNamed: ...


def parse_discrete(formula: str, columns: Mapping[str, int] | None = None) -> Discrete:
    """Create a discrete-time requirement from a formula and an optional variable-column mapping.

    If a variable-column mapping is provided, the created specification will expect states in the
    system trace to be a `Sequence[float]`. If the mapping is omitted then the specification will
    expect the states to be `dict[str, float]`. The discrete-time specification also imposes the
    following constraints on any `Trace` it evaluates:

    - The amount of time between each state must be equal
    - There must be at least two states in the trace

    :param requirement: The requirement to use to evaluate the `Trace`
    :param columns: The optional variable-column mapping
    :returns: A dense time specification
    """

    if columns:
        return DiscreteMapped(formula, dict(columns))

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
    """A dense-time STL specification using a variable-column map.

    The variable-column map is a mapping from the variable names in the formula to columns in the
    state, which is a vector.

    :param requirement: The formula to evaluate using the `Trace`
    :param columns: A mapping from variables names to columns of the state vector
    """

    def __init__(self, requirement: str, columns: dict[str, int]):
        self.requirement = requirement
        self.columns = columns

    def evaluate(self, trace: Trace[Sequence[float]]) -> Result[float, None]:
        times, states = _parse_trace(trace, self.columns)
        cost = _evaluate_dense(self.requirement, times, states)

        return Result(cost, None)


class DenseNamed(Specification[dict[str, float], float, None]):
    """A dense-time STL specification using the variable names in the state.

    :param requirement: The requirement to evaluate using the `Trace`
    """

    def __init__(self, requirement: str):
        self.requirement = requirement

    def evaluate(self, trace: Trace[dict[str, float]]) -> Result[float, None]:
        times, states = _parse_trace(trace)
        cost = _evaluate_dense(self.requirement, times, states)

        return Result(cost, None)


Dense: TypeAlias = Union[DenseMapped, DenseNamed]


@overload
def parse_dense(requirement: str, columns: Mapping[str, int]) -> DenseMapped: ...


@overload
def parse_dense(requirement: str, columns: None = ...) -> DenseNamed: ...


def parse_dense(requirement: str, columns: Mapping[str, int] | None = None) -> Dense:
    """Create a dense-time requirement from a formula and an optional variable-column mapping.

    If a variable-column mapping is provided, the created specification will expect states in the
    system trace to be a `Sequence[float]`. If the mapping is omitted then the specification will
    expect the states to be `dict[str, float]`.

    :param requirement: The requirement to use to evaluate the `Trace`
    :param columns: The optional variable-column mapping
    :returns: A dense time specification
    """

    if columns:
        return DenseMapped(requirement, dict(columns))

    return DenseNamed(requirement)


__all__ = ["parse_discrete", "parse_dense"]
