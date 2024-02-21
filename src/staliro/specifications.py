from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from math import inf
from typing import NewType, TypeVar

import numpy as np
from numpy.typing import NDArray

try:
    from rtamt import StlDenseTimeSpecification, StlDiscreteTimeSpecification
except ImportError:
    _has_rtamt = False
else:
    _has_rtamt = True

from .core import Specification, SpecificationError

StateT = TypeVar("StateT")
PredicateName = str
ColumnT = int
PredicateColumnMap = dict[PredicateName, ColumnT]


class StlSpecificationError(Exception):
    pass


_Times = NewType("_Times", NDArray[np.float64])
_States = NewType("_States", NDArray[np.float64])
_Parsed = tuple[_Times, _States]


def _parse_times_states(times: Sequence[float], states: Sequence[Sequence[float]]) -> _Parsed:
    times_ = _Times(np.array(times, dtype=np.float64))
    states_ = _States(np.array(states, dtype=np.float64))

    if times_.ndim != 1:
        raise StlSpecificationError("Times must be a 1-D vector")

    if states_.ndim != 2:
        raise StlSpecificationError("States must be a 2-D matrix")

    if states_.shape[0] == times_.size:
        return (times_, states_.T)
    elif states_.shape[1] == times_.size:
        return (times_, states_)
    else:
        raise StlSpecificationError("States must have one dimension that maches times length")


class StlSpecification(Specification[Sequence[float], float], ABC):
    @abstractmethod
    def __init__(self, requirement: str, column_map: PredicateColumnMap):
        ...

    @property
    def failure_cost(self) -> float:
        return -inf


class RTAMTDiscrete(StlSpecification):
    """STL logic specification that uses RTAMT discrete-time semantics to compute robustness.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, column_map: PredicateColumnMap):
        if "time" in column_map:
            raise SpecificationError("'time' cannot be used as a predicate name for RTAMT")

        self.phi = phi
        self.column_map = column_map

    def evaluate(self, states: Sequence[Sequence[float]], times: Sequence[float]) -> float:
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to use RTAMTDiscrete specification")

        times_, states_ = _parse_times_states(times, states)

        if times_.size < 2:
            raise RuntimeError("timestamps must have at least two samples to evaluate")

        spec = StlDiscreteTimeSpecification()

        for name in self.column_map:
            spec.declare_var(name, "float")

        period = times[1] - times[0]

        spec.set_sampling_period(round(period, 2), "s", 0.1)
        spec.spec = self.phi
        spec.parse()

        traces = {"time": list(times)}

        for name, column in self.column_map.items():
            traces[name] = list(states[column])

        robustness = spec.evaluate(traces)
        return robustness[0][1]


class RTAMTDense(StlSpecification):
    """STL logic specification that uses RTAMT dense-time semantics to compute robustness.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, column_map: PredicateColumnMap):
        self.phi = phi
        self.column_map = column_map

    def evaluate(self, states: Sequence[Sequence[float]], times: Sequence[float]) -> float:
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to use RTAMTDense specification")

        times_, states_ = _parse_times_states(times, states)
        spec = StlDenseTimeSpecification()

        for name in self.column_map:
            spec.declare_var(name, "float")

        spec.spec = self.phi
        spec.parse()

        map_items = self.column_map.items()
        traces = [
            (name, np.array([times_.tolist(), states_[column]]).T.tolist())
            for name, column in map_items
        ]

        robustness = spec.evaluate(*traces)
        return robustness[0][1]

