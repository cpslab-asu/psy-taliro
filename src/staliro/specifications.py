from __future__ import annotations

import statistics as stats
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Optional, TypeVar

import numpy as np
from numpy.typing import NDArray

try:
    from rtamt import (
        Language,
        Semantics,
        STLDenseTimeSpecification,
        STLDiscreteTimeSpecification,
    )
except ImportError:
    _has_rtamt = False
else:
    _has_rtamt = True

from .core import Specification, SpecificationError

try:
    from .parser import parse
except:
    _can_parse = False
else:
    _can_parse = True


StateT = TypeVar("StateT")
PredicateName = str
ColumnT = int
PredicateColumnMap = Dict[PredicateName, ColumnT]


def _valid_trajectories_array(trajectories: NDArray[Any], row_len: int) -> Optional[str]:
    if not trajectories.ndim == 2:
        return "trajectories array must be 2-dimensional"

    if not trajectories.shape[1] == row_len:
        return f"trajectory array must have {row_len} columns"

    return None


class StlSpecification(Specification[StateT], ABC):
    @abstractmethod
    def __init__(self, requirement: str, column_map: PredicateColumnMap):
        ...


class TLTK(StlSpecification[NDArray[np.float_]]):
    """STL logic specification that uses TLTK to compute robustness values.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, column_map: PredicateColumnMap):
        if not _can_parse:
            raise RuntimeError(
                "TLTK specifications require parsing functionality. Please refer to the documentation for how to enable parsing."
            )

        tltk_obj = parse(phi, list(column_map.keys()))

        if tltk_obj is None:
            raise SpecificationError("could not parse formula")

        self.tltk_obj = tltk_obj
        self.column_map = column_map

    def evaluate(self, states: NDArray[np.float_], times: NDArray[np.float_]) -> float:
        trajectories_err = _valid_trajectories_array(states, times.size)

        if trajectories_err is not None:
            raise SpecificationError(trajectories_err)

        map_items = self.column_map.items()
        traces = {name: np.array(states[column], dtype=np.float64) for name, column in map_items}
        timestamps = np.array(times, dtype=np.float32)

        self.tltk_obj.reset()
        self.tltk_obj.eval_interval(traces, timestamps)

        return self.tltk_obj.robustness


def _step_widths(times: NDArray[np.float_]) -> Iterable[float]:
    """Compute the distance between adjacent elements."""

    for i in range(len(times) - 2):
        yield abs(times[i] - times[i + 1])


class RTAMTDiscrete(StlSpecification[NDArray[np.float_]]):
    """STL logic specification that uses RTAMT Discrete-Time semantics to computer robustness.

    Attributes:
        formula: The specification requirement
        predicates: A set of Predicates used in the requirement.
    """

    def __init__(self, formula: str, predicate_map: PredicateColumnMap):
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to used the RTAMTDiscrete specification")

        self._obj = STLDiscreteTimeSpecification(
            Semantics.STANDARD,
            language=Language.PYTHON
        )

        self._obj.spec = formula
        self._predicate_map = predicate_map

        for name in predicate_map.keys():
            self._obj.declare_var(name, "float")

    def evaluate(self, states: NDArray[np.float_], timestamps: NDArray[np.float_]) -> float:
        """Evaluate the robustness of the specification against some trajectories.

        Arguments:
            states:
            timestamps:
        """

        self._obj.set_sampling_period(round(timestamps[1] - timestamps[0], 3), "s", 0.1)
        self._obj.parse()

        if len(timestamps) < 2:
            raise RuntimeError("Two samples must be present to evaluate")

        timestamps = np.array(timestamps, dtype=np.float64, ndmin=2)
        if timestamps.shape[0] != 1:
            raise RuntimeError("Please provide timestamps as a single row")

        states = np.array(states, dtype=np.float64, ndmin=2)
        if states.shape[0] != timestamps.shape[0]:
            raise RuntimeError("The length of the timestamps and state samples must match")

        trajectories = {"time": timestamps[0].tolist()}
        for name, column in self._predicate_map.items():
            trajectories[name] = states[column].tolist()

        robustness = self._obj.evaluate(trajectories)
        return robustness[0][1]

class RTAMTDense(StlSpecification[NDArray[np.float_]]):
    """STL logic specification that uses RTAMT Dense-Time semantics to computer robustness.

    Attributes:
        formula: The specification requirement
        predicates: A set of Predicates used in the requirement.
    """

    def __init__(self, formula: str, predicate_map: PredicateColumnMap):
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to used the RTAMTDense specification")

        self._obj = STLDenseTimeSpecification(
            Semantics.STANDARD,
            language=Language.PYTHON
        )

        self._obj.spec = formula
        self._predicate_map = predicate_map

        for name in predicate_map.keys():
            self._obj.declare_var(name, "float")

    def evaluate(self, states: NDArray[np.float_], timestamps: NDArray[np.float_]) -> float:
        """Evaluate the robustness of the specification against some trajectories.

        Arguments:
            states:
            timestamps:
        """

        self._obj.parse()

        if len(timestamps) < 2:
            raise RuntimeError("Two samples must be present to evaluate")

        timestamps = np.array(timestamps, dtype=np.float64, ndmin=2)
        if timestamps.shape[0] != 1:
            raise RuntimeError("Please provide timestamps as a single row")

        states = np.array(states, dtype=np.float64, ndmin=2)
        if states.shape[0] != timestamps.shape[0]:
            raise RuntimeError("The length of the timestamps and state samples must match")

        pmap = self._predicate_map.items()
        trajectories = [
            (name, np.array([timestamps[0], states[column]]).T.tolist()) for name, column in pmap
        ]

        robustness = self._obj.evaluate(*trajectories)
        return robustness[0][1]
