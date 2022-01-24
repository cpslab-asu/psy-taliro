from __future__ import annotations

import statistics as stats
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable, Optional, TypeVar

import numpy as np
from numpy.typing import NDArray

try:
    from rtamt import (
        LTLPastifyException,
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
    if not isinstance(trajectories, np.ndarray):
        return "trajectories must be provided as an NDArray"

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
    """STL logic specification that uses RTAMT discrete-time semantics to compute robustness.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, column_map: PredicateColumnMap):
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to use RTAMTDiscrete specification")

        if "time" in column_map:
            raise SpecificationError("'time' cannot be used as a predicate name for RTAMT")

        self.rtamt_obj = STLDiscreteTimeSpecification(Semantics.STANDARD)

        self.rtamt_obj.spec = phi
        self.column_map = column_map

        for name in column_map:
            self.rtamt_obj.declare_var(name, "float")

    def evaluate(self, states: NDArray[np.float_], times: NDArray[np.float_]) -> float:
        trajectories_err = _valid_trajectories_array(states, times.size)

        if trajectories_err is not None:
            raise SpecificationError(trajectories_err)

        self.rtamt_obj.reset()

        period = stats.mean(_step_widths(times))
        self.rtamt_obj.set_sampling_period(round(period, 2), "s", 0.1)

        # parse AFTER declaring variables and setting sampling period
        self.rtamt_obj.parse()

        try:
            self.rtamt_obj.pastify()
        except LTLPastifyException:
            pass

        traces = {"time": times.tolist()}

        for name, column in self.column_map.items():
            traces[name] = states[column].tolist()

        # traces: Dict['time': timestamps, 'variable'(s): trajectories]
        robustness = self.rtamt_obj.evaluate(traces)

        return robustness[-1][1]


class RTAMTDense(StlSpecification[NDArray[np.float_]]):
    """STL logic specification that uses RTAMT dense-time semantics to compute robustness.

    Attributes:
        phi: The specification requirement
        predicates: A set of Predicate(s) used in the requirement
    """

    def __init__(self, phi: str, column_map: PredicateColumnMap):
        if not _has_rtamt:
            raise RuntimeError("RTAMT must be installed to use RTAMTDense specification")

        self.rtamt_obj = STLDenseTimeSpecification(Semantics.STANDARD)
        self.column_map = column_map
        self.rtamt_obj.spec = phi

        for name in column_map:
            self.rtamt_obj.declare_var(name, "float")

    def evaluate(self, states: NDArray[np.float_], times: NDArray[np.float_]) -> float:
        trajectories_err = _valid_trajectories_array(states, times.size)

        if trajectories_err is not None:
            raise SpecificationError(trajectories_err)

        self.rtamt_obj.reset()

        # parse AFTER declaring variables
        self.rtamt_obj.parse()

        try:
            self.rtamt_obj.pastify()
        except LTLPastifyException:
            pass

        map_items = self.column_map.items()
        traces = [
            (name, np.array([times, states[column]]).T.tolist()) for name, column in map_items
        ]

        robustness = self.rtamt_obj.evaluate(*traces)

        return robustness[-1][1]
