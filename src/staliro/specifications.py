from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar

import numpy as np
from numpy.typing import NDArray

try:
    from rtamt import Language, Semantics, STLDenseTimeSpecification, STLDiscreteTimeSpecification
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


def _validate_trajectories(states: NDArray[Any], timestamps: NDArray[Any]) -> Optional[str]:
    if timestamps.shape[0] != 1:
        raise SpecificationError("please provide timestamps as a single row")

    if states.shape[0] != timestamps.shape[0]:
        raise SpecificationError("the length of the timestamps and state samples must match")


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

        self._tltk_obj = tltk_obj
        self.column_map = column_map

    def evaluate(self, states: NDArray[np.float_], timestamps: NDArray[np.float_]) -> float:
        """Evaluate the robustness of the specification against some trajectories.

        Arguments:
            states:
            timestamps:
        """

        states = np.array(states, dtype=np.float64, ndmin=2)
        timestamps = np.array(timestamps, dtype=np.float32, ndmin=2)

        _validate_trajectories(states, timestamps)

        colmap = self.column_map.items()
        traces = {name: states[column] for name, column in colmap}
        timestamps = timestamps[0]

        self._tltk_obj.reset()
        self._tltk_obj.eval_interval(traces, timestamps)

        return self._tltk_obj.robustness


class RTAMTDiscrete(StlSpecification[NDArray[np.float_]]):
    """STL logic specification that uses RTAMT Discrete-Time semantics to computer robustness.

    Attributes:
        formula: The specification requirement
        predicates: A set of Predicates used in the requirement.
    """

    def __init__(self, formula: str, column_map: PredicateColumnMap):
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to used the RTAMTDiscrete specification")

        self._rtamt_obj = STLDiscreteTimeSpecification(Semantics.STANDARD, language=Language.PYTHON)

        self._rtamt_obj.spec = formula
        self._column_map = column_map

        for name in column_map.keys():
            self._rtamt_obj.declare_var(name, "float")

    def evaluate(self, states: NDArray[np.float_], timestamps: NDArray[np.float_]) -> float:
        """Evaluate the robustness of the specification against some trajectories.

        Arguments:
            states:
            timestamps:
        """

        self._rtamt_obj.set_sampling_period(round(timestamps[1] - timestamps[0], 3), "s", 0.1)
        self._rtamt_obj.parse()

        if len(timestamps) < 2:
            raise RuntimeError("Two samples must be present to evaluate")

        states = np.array(states, dtype=np.float64, ndmin=2)
        timestamps = np.array(timestamps, dtype=np.float64, ndmin=2)

        _validate_trajectories(states, timestamps)

        trajectories = {"time": timestamps[0].tolist()}
        for name, column in self._column_map.items():
            trajectories[name] = states[column].tolist()

        robustness = self._rtamt_obj.evaluate(trajectories)
        return robustness[0][1]


class RTAMTDense(StlSpecification[NDArray[np.float_]]):
    """STL logic specification that uses RTAMT Dense-Time semantics to computer robustness.

    Attributes:
        formula: The specification requirement
        predicates: A set of Predicates used in the requirement.
    """

    def __init__(self, formula: str, column_map: PredicateColumnMap):
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to used the RTAMTDense specification")

        self._rtamt_obj = STLDenseTimeSpecification(Semantics.STANDARD, language=Language.PYTHON)

        self._rtamt_obj.spec = formula
        self._column_map = column_map

        for name in column_map.keys():
            self._rtamt_obj.declare_var(name, "float")

    def evaluate(self, states: NDArray[np.float_], timestamps: NDArray[np.float_]) -> float:
        """Evaluate the robustness of the specification against some trajectories.

        Arguments:
            states:
            timestamps:
        """

        self._rtamt_obj.parse()

        states = np.array(states, dtype=np.float64, ndmin=2)
        timestamps = np.array(timestamps, dtype=np.float64, ndmin=2)

        _validate_trajectories(states, timestamps)

        colmap = self._column_map.items()
        trajectories = [
            (name, np.array([timestamps[0], states[column]]).T.tolist()) for name, column in colmap
        ]

        robustness = self._rtamt_obj.evaluate(*trajectories)
        return robustness[0][1]
