from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import TypeAlias, TypeVar, cast, overload

import attrs
from rtamt import StlDenseTimeSpecification, StlDiscreteTimeSpecification
from typing_extensions import Self, override

from ..cost_func import Result
from ..models import Trace
from .specification import Specification

_Times: TypeAlias = list[float]
_States: TypeAlias = dict[str, list[float]]
_ColumnMap: TypeAlias = Mapping[str, int]

T = TypeVar("T", Mapping[str, float], Sequence[float])


def _parse_named(states: Iterable[Mapping[str, float]]) -> _States:
    states_iter = iter(states)
    state = next(states_iter)
    vars = {
        name: [value] for name, value in state.items()
    }

    for state in states_iter:
        for name, value in state.items():
            vars[name].append(value)

    return vars


def _parse_mapped(states: Iterable[Sequence[float]], columns: dict[str, int]) -> _States:
    states_iter = iter(states)
    state = next(states_iter)
    vars = {
        name: [state[idx]] for name, idx in columns.items()
    }

    for state in states_iter:
        for name, idx in columns.items():
            vars[name].append(state[idx])

    return vars


@attrs.define()
class DiscreteRequirement:
    formula: str

    def evaluate(self, times: Iterable[float], states: _States) -> float:
        times = list(times)

        try:
            period = times[1] - times[0]
        except IndexError as e:
            raise ValueError("trace must have at least two states to be evaluated") from e

        spec = StlDiscreteTimeSpecification()
        spec.spec = self.formula

        for name in states:
            spec.declare_var(name, "float")

        spec.set_sampling_period(round(period, 2), "s", 0.1)
        spec.parse()

        robustness = spec.evaluate({"time": times, **states})
        return robustness[0][1]

    def evaluate_named(self, trace: Trace[Mapping[str, float]]) -> float:
        return self.evaluate(trace.times, _parse_named(trace.states))

    def evaluate_mapped(self, trace: Trace[Sequence[float]], columns: dict[str, int]) -> float:
        return self.evaluate(trace.times, _parse_mapped(trace.states, columns))


@attrs.define()
class Discrete(Specification[T, float, None]):
    requirement: DiscreteRequirement


@attrs.define()
class DiscreteMapped(Discrete[Sequence[float]]):
    """A discrete-time STL specification using a variable-column map.

    The variable-column map is a mapping from the variable names in the formula to columns in the
    state, which is a vector. In addition, the trace used for evaluation must fulfill the following
    criteria:

    - There is an equal amount of time between each state in the trace
    - There are at least two states in the trace

    :param requirement: The formula to evaluate using the `Trace`
    :param columns: A mapping from variables names to columns of the state vector
    """

    columns: dict[str, int]

    def evaluate(self, trace: Trace[Sequence[float]]) -> Result[float, None]:
        return Result(self.requirement.evaluate_mapped(trace, self.columns), None)


@attrs.define()
class DiscreteNamed(Discrete[Mapping[str, float]]):
    """A discrete-time STL specification using the variable names in the state.

    The trace used for evaluation must fulfill the following criteria:

    - There is an equal amount of time between each state in the trace
    - There are at least two states in the trace

    :param requirement: The formula to evaluate using the `Trace`
    """

    @override
    def evaluate(self, trace: Trace[Mapping[str, float]]) -> Result[float, None]:
        return Result(self.requirement.evaluate_named(trace), None)


@overload
def discrete(formula: str) -> DiscreteNamed: ...


@overload
def discrete(formula: str, *, columns: Mapping[str, int]) -> DiscreteMapped: ...


def discrete(formula: str, *, columns: _ColumnMap | None = None) -> DiscreteMapped | DiscreteNamed:
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

    requirement = DiscreteRequirement(formula)

    if columns:
        return DiscreteMapped(requirement, dict(columns))

    return DiscreteNamed(requirement)


@attrs.define()
class DenseRequirement:
    formula: str

    def evaluate(self, times: Iterable[float], vars: _States) -> float:
        spec = StlDenseTimeSpecification()
        spec.spec = self.formula

        for name in vars:
            spec.declare_var(name, "float")

        spec.parse()

        traces = {
            name: list(zip(times, values, strict=True)) for name, values in vars.items()
        }
        robustness = spec.evaluate(*traces.items())

        return robustness[0][1]

    def evaluate_named(self, trace: Trace[Mapping[str, float]]) -> float:
        return self.evaluate(trace.times, _parse_named(trace.states))

    def evaluate_mapped(self, trace: Trace[Sequence[float]], columns: dict[str, int]) -> float:
        return self.evaluate(trace.times, _parse_mapped(trace.states, columns))


@attrs.define()
class Dense(Specification[T, float, None]):
    requirement: DenseRequirement


@attrs.define()
class DenseMapped(Dense[Sequence[float]]):
    """A dense-time STL specification using a variable-column map.

    The variable-column map is a mapping from the variable names in the formula to columns in the
    state, which is a vector.

    :param requirement: The formula to evaluate using the `Trace`
    :param columns: A mapping from variables names to columns of the state vector
    """

    columns: dict[str, int]

    @override
    def evaluate(self, trace: Trace[Sequence[float]]) -> Result[float, None]:
        return Result(self.requirement.evaluate_mapped(trace, self.columns), None)


@attrs.define()
class DenseNamed(Dense[Mapping[str, float]]):
    """A dense-time STL specification using the variable names in the state.

    :param requirement: The requirement to evaluate using the `Trace`
    """

    @override
    def evaluate(self, trace: Trace[Mapping[str, float]]) -> Result[float, None]:
        return Result(self.requirement.evaluate_named(trace), None)


@overload
def dense(formula: str) -> DenseNamed: ...


@overload
def dense(formula: str, *, columns: Mapping[str, int]) -> DenseMapped: ...


def dense(formula: str, *, columns: _ColumnMap | None = None) -> DenseNamed | DenseMapped:
    """Create a dense-time requirement from a formula and an optional variable-column mapping.

    If a variable-column mapping is provided, the created specification will expect states in the
    system trace to be a `Sequence[float]`. If the mapping is omitted then the specification will
    expect the states to be `dict[str, float]`.

    :param requirement: The requirement to use to evaluate the `Trace`
    :param columns: The optional variable-column mapping
    :returns: A dense time specification
    """

    requirement = DenseRequirement(formula)

    if columns:
        return DenseMapped(requirement, dict(columns))

    return DenseNamed(requirement)


__all__ = ["Discrete", "Dense"]
